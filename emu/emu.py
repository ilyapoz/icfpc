#!/usr/bin/python
import argparse
import numpy
import json
import sys
import os
import unittest
import math

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
        rotation += 600
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

        left_coord = min([x + (y - min_y) % 2 * 0.5 for x, y in field_space])
        right_coord = max([x + 1 + (y - min_y) % 2 * 0.5 for x, y in field_space])

        self.starting_position = (math.floor((width - (left_coord + right_coord)) / 2), -min_y)


class Position:
    unit = None
    pivot = (0, 0)
    rotation = 0 # cw rotation

    def __init__(self, unit):
        self.unit = unit

    def field_space(self):
        for cell in self.unit.cells:
            rot = Unit.rotate(cell, self.rotation)
            shift = Unit.field_to_unit_space(self.pivot)
            shifted = (rot[0] + shift[0], rot[1] + shift[1])
            yield Unit.unit_to_field_space(shifted)

    def draw(self, board):
        board.pivot = self.pivot
        for x, y in self.field_space():
            board.unit[x, y] = True

    def hash(self):
        return hash(str(sorted(list(self.field_space()))))


class Board:
    def __init__(self, width, height, filled):
        self.filled = filled
        self.width = width
        self.height = height

        self.field = numpy.zeros((width, height), int)
        for cell in filled:
            self.field[cell['x'], cell['y']] = 1

        self.clear_unit()

    def clear_unit(self):
        self.unit = numpy.zeros((self.width, self.height), int)
        self.pivot = (-1, -1)

    def fix_unit(self):
        self.field = self.field + self.unit
        pass

    def create_unit(self, unit):
        self.clear_unit()

    def draw(self, expr, ext=0):
        for y in xrange(0, self.height):
            if y % 2:
                print ' ' * ext,

            for x in xrange(0, self.width):
                print expr(x, y) + ' ' * ext,

            print '\n' * ext

    def draw_field(self, ext=0):
        self.draw(lambda x, y: self.sym(x, y), ext)

    def sym(self, x, y):
        if self.field[x, y]:
            return '#'

        is_pivot = (x, y) == self.pivot
        is_unit = self.unit[x, y]

        return self.syms[is_unit][is_pivot]


    syms = (('.', 'o'), ('*', '@'))

class Game:
    class MoveResult:
        Loss = 0
        Lock = 1
        Continue = 2

    def __init__(self, board, unit_generator):
        self.board = board
        self.unit_generator = unit_generator

    def try_sw(self):
        """
            returns MoveResult
        """
        pass

    def try_se(self):
        pass

    def try_cw(self):
        pass

    def try_ccw(self):
        pass

    def undo(self):
        pass

    def redo(self):
        pass


class UnitGenerator:
    def __init__(self, units, source_seed, source_length):
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
    def __init__(self, board_generator, units, source_seeds, source_length):
        self.current_seed_index = -1
        self.source_seeds = source_seeds
        self.source_length = source_length
        self.units = units
        self.board_generator = board_generator

    def __iter__(self):
        return self

    def next(self):
        self.current_seed_index += 1
        if self.current_seed_index == len(self.source_seeds):
            raise StopIteration
        return Game(self.board_generator(), UnitGenerator(self.units, self.source_seeds[self.current_seed_index], self.source_length))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f')
    parser.add_argument('--unit', type=int, default=0)

    args = parser.parse_args()

    input_data = json.load(open(args.file))

    board = Board(input_data['width'], input_data['height'], input_data['filled'])
    units = map(lambda x: Unit(x['members'], x['pivot']), input_data['units'])
    for u in units:
        u.calc_starting_position(board.width)

    unit_index = args.unit
    unit = units[unit_index]

    pos = Position(unit)
    pos.pivot = (5, 5)
    pos.rotation = 0

    pos.pivot = unit.starting_position
    pos.draw(board)
    board.draw_field()
