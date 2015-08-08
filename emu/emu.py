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
    def __init__(self, width, height, filled=None, field=None):
        self.width = width
        self.height = height
        self.field = numpy.zeros((width, height), int) if field is None else numpy.copy(field)
        if filled is not None:
            for cell in filled:
                self.field[cell['x'], cell['y']] = 1

    def in_board(self, cell):
        return 0 <= cell[0] < self.width and 0 <= cell[1] < self.height

    def filled_lines(self):
        return numpy.nonzero(numpy.sum(self.field, 0) == self.width)[0].tolist()

    def __clear_line(self, y):
        # Move one line down
        for yy in range(y - 1, -1, -1):
            for x in range(0, self.width):
                self.field[x, yy + 1] = self.field[x, yy]
        for x in range(0, self.width):
            self.field[x, 0] = 0

    def __clear_filled_lines(self):
        filled = self.filled_lines()
        for l in filled:
            self.__clear_line(l)

        return len(filled)

    def fix_unit_and_clear(self, pos):
        new_board = Board(self.width, self.height, field = self.field)
        for x, y in pos.field_space():
            new_board.field[x, y] = 1

        return (new_board, new_board.__clear_filled_lines())

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


class PersistentStack:
    def __init__(self, head=None, tail=None):
        self.head = head
        self.tail = tail

    def items(self):
        if self.empty():
            return
        if self.head is not None:
            for item in self.head.items():
                yield item
        yield self.tail

    def push(self, value):
        return PersistentStack(self, value)

    def empty(self):
        return self.tail is None


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

    class State:
        def __init__(self, unit_pos, board, score, visited_positions):
            self.unit_pos = unit_pos
            self.board = board
            self.score = score
            self.visited_positions = visited_positions

    def __init__(self, board, unit_generator):
        self.units = list(unit_generator)
        self.game_ended = False
        self.state_stack = []
        self.switch_to_next_unit(board, 0)

    def switch_to_next_unit(self, board, score):
        cur_unit_index = -1 if len(self.state_stack) == 0 else self.units.index(self.cur_unit_pos().unit)
        next_unit_index = cur_unit_index + 1
        if next_unit_index == len(self.units):
            self.game_ended = True
            logging.debug('Game ended because no more pieces are available' % next_unit_index)
            return

        next_unit = self.units[next_unit_index]
        next_unit_pos = Position(next_unit, next_unit.starting_position, 0)
        if next_unit_index == 0 or self.try_pos(next_unit_pos) == Game.MoveResult.Continue:
            self.state_stack.append(Game.State(next_unit_pos, board, score, PersistentStack()))
            logging.debug('Piece %d started' % next_unit_index)
        else:
            self.game_ended = True
            logging.debug('Game ended because piece %d cannot be placed' % next_unit_index)

    def ended(self):
        return self.game_ended

    def score(self):
        return self.state_stack[-1].score

    def cur_unit_pos(self):
        return None if self.game_ended else self.state_stack[-1].unit_pos

    def board(self):
        return self.state_stack[-1].board

    def commit_pos(self, pos):
        move_result = self.try_pos(pos)
        assert move_result != Game.MoveResult.Loss

        if move_result == Game.MoveResult.Lock:
            (new_board, lines_cleared) = self.state_stack[-1].board.fix_unit_and_clear(self.cur_unit_pos())
            self.switch_to_next_unit(new_board, 0)  # TODO: compute new score
        elif move_result == Game.MoveResult.Continue:
            self.state_stack.append(Game.State(
                pos,
                self.state_stack[-1].board,
                self.state_stack[-1].score,
                self.state_stack[-1].visited_positions.push((pos.pivot[0], pos.pivot[1], pos.rotation))))
        else:
            assert False

    def try_pos(self, pos):
        if (pos.pivot[0], pos.pivot[1], pos.rotation) in self.state_stack[-1].visited_positions.items():
            return Game.MoveResult.Loss

        for x, y in pos.field_space():
            if not self.board().in_board((x, y)) or self.board().field[x, y]:
                return Game.MoveResult.Lock

        return Game.MoveResult.Continue

    def undo(self):
        if len(self.state_stack) > 1:
            self.state_stack.pop()


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
        logging.debug('Game with seed %d started' % self.current_seed_index)
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

    board.draw_field(pos)
