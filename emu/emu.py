#!/usr/bin/python
import argparse
import numpy
import json
import sys
import os
import unittest
import math
import logging

logging.basicConfig(filename='emu.log', level=logging.DEBUG)

class Unit:
    def __init__(self, cells, pivot):
        pivot = Unit.field_to_unit_space((pivot['x'], pivot['y']))

        self.cells = map(lambda x: Unit.field_to_unit_space((x['x'], x['y'])), cells)

        self.cells = map(lambda x: (x[0] - pivot[0], x[1] - pivot[1]), self.cells)
        self.symmetry_class = self.calc_symmetry_class()

    @staticmethod
    def field_to_unit_space(coords):
        return (coords[0] - coords[1] / 2, coords[1])

    @staticmethod
    def unit_to_field_space(coords):
        return (coords[0] + coords[1] / 2, coords[1])

    @staticmethod
    def rot60(cell):
        return (-cell[1], cell[0] + cell[1])

    @staticmethod
    def rotate(cell, rotation):
        rotation %= 6
        answer = cell
        for i in range(rotation):
            answer = Unit.rot60(answer)

        return answer

    def calc_symmetry_class(self):
        pos = Position(self)
        hash_0 = pos.hash()
        pos.rotation = 1
        while hash_0 != pos.hash():
            pos.rotation += 1

        return pos.rotation

    def extent(self):
        return (
            max(x[0] for x in self.cells) - min(x[0] for x in self.cells) + 1,
            max(x[1] for x in self.cells) - min(x[1] for x in self.cells) + 1
        )

    def calc_starting_position(self, width):
        min_y = min([x[1] for x in self.cells])

        pos = Position(self);
        pos.pivot = (0, -min_y)
        field_space = list(pos.field_space())
        field_width = width + 0.5

        left_coord = min([x + y % 2 * 0.5 for x, y in field_space])
        right_coord = max([x + 1 + y % 2 * 0.5 for x, y in field_space])

        self.starting_position = (math.floor((field_width - (left_coord + right_coord)) / 2), -min_y)


class Position:
    def __init__(self, unit, pivot=(0, 0), rotation=0):
        self.unit = unit
        self.pivot = pivot
        self.rotation = rotation

    def field_space(self):
        for cell in self.unit.cells:
            rot = Unit.rotate(cell, self.rotation)
            shift = Unit.field_to_unit_space(self.pivot)
            shifted = (rot[0] + shift[0], rot[1] + shift[1])
            yield Unit.unit_to_field_space(shifted)

    def west(self):
        return Position(self.unit, (self.pivot[0]-1, self.pivot[1]), self.rotation)

    def east(self):
        return Position(self.unit, (self.pivot[0]+1, self.pivot[1]), self.rotation)

    def south_west(self):
        unit = Unit.field_to_unit_space(self.pivot)
        unit = (unit[0] - 1, unit[1] + 1)
        return Position(self.unit, Unit.unit_to_field_space(unit), self.rotation)

    def south_east(self):
        unit = Unit.field_to_unit_space(self.pivot)
        unit = (unit[0], unit[1] + 1)
        return Position(self.unit, Unit.unit_to_field_space(unit), self.rotation)

    def cw(self):
        return Position(self.unit, self.pivot, (self.rotation + 1) % self.unit.symmetry_class)

    def ccw(self):
        logging.debug('%d', self.rotation)
        return Position(self.unit, self.pivot, (self.rotation - 1) % self.unit.symmetry_class)

    def hash(self):
        return hash(str(sorted(list(self.field_space()))))


class Board:
    def __init__(self, width, height, filled):
        self.width = width
        self.height = height

        self.field = numpy.zeros((width, height), int)
        for cell in filled:
            self.field[cell['x'], cell['y']] = 1

    def in_board(self, cell):
        return 0 <= cell[0] < self.width and 0 <= cell[1] < self.height

    def filled_lines(self):
        return numpy.nonzero(numpy.sum(self.field, 0) == self.width)[0].tolist()

    def clear_line(self, y):
        # Move one line down
        for yy in range(y - 1, -1, -1):
            for x in range(0, self.width):
                self.field[x, yy + 1] = self.field[x, yy]
        for x in range(0, self.width):
            self.field[x, 0] = 0

    def clear_filled_lines(self):
        filled = self.filled_lines()
        for l in filled:
            self.clear_line(l)

        return len(filled)

    def fix_unit_and_clear(self, pos):
        for x, y in pos.field_space():
            self.field[x, y] = 1

        return self.clear_filled_lines()


    def get_field_str_impl(self, expr, ext=0):
        result = ''
        for y in xrange(0, self.height):
            if y % 2:
                result += ' ' * (ext + 1)

            for x in xrange(0, self.width):
                result += expr(x, y) + ' ' * (ext + 1)

            result += '\n' * (ext + 1)
        return result

    def get_field_str(self, pos, ext=0):
        return self.get_field_str_impl(lambda x, y: self.sym(x, y, pos), ext)

    def draw_field(self, pos, ext=0):
        print self.get_field_str(pos, ext)

    def sym(self, x, y, pos):
        if self.field[x, y]:
            return '#'

        is_pivot = (x, y) == pos.pivot if pos else False
        is_unit = (x, y) in pos.field_space() if pos else False

        return self.syms[is_unit][is_pivot]

    syms = (('.', 'o'), ('*', '@'))


class Game:
    class MoveResult:
        Loss = 'Loss'
        Lock = 'Lock'
        Continue = 'Ok'

    class GameOver(Exception):
        pass

    @staticmethod
    def compute_points(unit_size, lines_cleared, lines_cleared_prev):
        points = unit_size + 100 * (1 + lines_cleared) * lines_cleared / 2
        line_bonus = (lines_cleared_prev - 1) * points / 10 if lines_cleared_prev > 1 else 0
        return points + line_bonus

    def __init__(self, board, unit_generator):
        self.board = board
        self.unit_generator = unit_generator
        self.cur_score = 0

        self.cur_unit = None
        self.try_get_next_unit()

    def try_get_next_unit(self):
        try:
            self.prev = set()
            self.cur_unit = self.unit_generator.next()
            pos = Position(self.cur_unit, self.cur_unit.starting_position, 0)
            if self.try_pos(pos):
                self.cur_position = pos
            else:
                self.cur_init = None
        except StopIteration:
            self.cur_unit = None

    def ended(self):
        return self.cur_unit is None

    def score(self):
        return self.cur_score

    def commit_pos(self, pos):
        move_result = self.try_pos(pos)
        assert move_result != Game.MoveResult.Loss

        if move_result == Game.MoveResult.Lock:
            self.board.fix_unit_and_clear()
            self.try_get_next_unit()
        elif move_result == Game.MoveResult.Continue:
            pos.draw(self.board)
            self.cur_position = pos
            self.prev.add((pos.pivot[0], pos.pivot[1], pos.rotation))
        else:
            assert False

    def try_pos(self, pos):
        if (pos.pivot[0], pos.pivot[1], pos.rotation) in self.prev:
            return Game.MoveResult.Loss

        for x, y in pos.field_space():
            if not self.board.in_board((x, y)) or self.board.field[x, y]:
                return Game.MoveResult.Lock

        return Game.MoveResult.Continue

    def undo(self):
        raise NotImplemented

    def redo(self):
        raise NotImplemented


class UnitGenerator:
    def __init__(self, units, source_seed, source_length):
        self.source_seed = source_seed
        self.current_seed = source_seed
        self.emitted_unit_count = 0
        self.source_length = source_length
        self.units = units

    def __iter__(self):
        return self

    @staticmethod
    def get_bits(number, min_index, max_index):
        number = number >> min_index << min_index
        number = ((number << (32 - max_index)) & 0xFFFFFFFF) >> (32 - max_index)
        return number

    def next(self):
        if self.emitted_unit_count == self.source_length:
            raise StopIteration
        self.emitted_unit_count += 1
        random_number = UnitGenerator.get_bits(self.current_seed, 16, 31) >> 16
        index = random_number % len(self.units)
        self.current_seed = (self.current_seed * 1103515245 + 12345) % (2 ** 32)
        return self.units[index]


class GameGenerator:
    def __init__(self, config):
        self.current_seed_index = -1
        self.source_seeds = config['sourceSeeds']
        self.source_length = config['sourceLength']
        self.config = config

        self.units = [Unit(unit_cfg['members'], unit_cfg['pivot']) for unit_cfg in config['units']]
        for unit in self.units:
            unit.calc_starting_position(config['width'])

    def __iter__(self):
        return self

    def next(self):
        self.current_seed_index += 1
        if self.current_seed_index == len(self.source_seeds):
            raise StopIteration
        return Game(Board(self.config['width'], self.config['height'], self.config['filled']),
                    UnitGenerator(self.units, self.source_seeds[self.current_seed_index], self.source_length))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f')
    parser.add_argument('--unit', type=int, default=0)

    args = parser.parse_args()

    config = json.load(open(args.file))

    game = GameGenerator(config).next()

    board = Board(config['width'], config['height'], config['filled'])
    units = map(lambda x: Unit(x['members'], x['pivot']), config['units'])
    for u in units:
        u.calc_starting_position(board.width)

    unit_index = args.unit
    unit = units[unit_index]

    pos = Position(unit)
    pos.pivot = unit.starting_position
    pos.rotation = 0

    pos = pos.south_west()

    board.clear_line(11)
    board.clear_line(13)
    board.clear_line(13)
    board.draw_field(pos)
    logging.debug(board.filled_lines())
