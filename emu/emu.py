#!/usr/bin/python
import argparse
import numpy
import json
import sys
import os
import unittest

class Unit:
    def __init__(self, cells, pivot):
        pivot = Unit.field_to_piece_space((pivot['x'], pivot['y']))

        self.cells = map(lambda x: [x['x'] - pivot[0], x['y'] - pivot[0]], cells)
        self.rotation = 0

    def cw(self):
        self.rotation = self.rotation - 1

    def ccw(self):
        self.rotation = self.rotation + 1

    def sw(self):
        pass

    def se(self):
        pass

    def w(self):
        pass

    def e(self):
        pass

    def draw(self, board, position):
        for x, y in self.cells:
            board

    @staticmethod
    def field_to_piece_space(coords):
        return (coords[0] - coords[1] / 2, coords[1])

    @staticmethod
    def piece_to_field_space(coords):
        return (coords[0] + coords[1] / 2, coords[1])

    @staticmethod
    def rotate(cell, rotation):
        pass

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

    def fix_unit(self):
        self.field = self.field + self.unit
        pass

    def create_unit(self, unit):
        pass

    def draw(self):
        for y in xrange(0, self.height):
            if y % 2:
                print '',

            for x in xrange(0, self.width):
                print 'o' if self.field[x, y] else '*' if self.unit[x, y] else '.',

            print

class Game:
    class MoveResult:
        Loss = 0
        Lock = 1
        Continue = 2

    def __init__(self, board, units):
        self.board = board
        self.units = units

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

class TestUnit(unittest.TestCase):
    def test_sanity(self):
        for x in range(-100, 100):
            for y in range(-100, 100):
                to_piece = Unit.field_to_piece_space((x, y))
                to_field = Unit.piece_to_field_space(to_piece)

                self.assertEqual(to_field, (x, y))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f')
    parser.add_argument('--test', '-t')

    args = parser.parse_args()

    input_data = json.load(open(args.file))

    board = Board(input_data['width'], input_data['height'], input_data['filled'])
    units = map(lambda x: Unit(x['members'], x['pivot']), input_data['units'])

    if args.test:
        unittest.main()
        sys.exit(0)

    board.create_unit(units[0])
    board.draw()
    board.fix_unit()

    print Unit.field_to_piece_space((0, 2))
    print Unit.piece_to_field_space((0, 2))
