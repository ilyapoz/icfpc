#!/usr/bin/python
import argparse
import numpy
import json
import sys
import os
import unittest

class Unit:
    def __init__(self, cells, pivot):
        pivot = Unit.field_to_unit_space((pivot['x'], pivot['y']))

        self.cells = map(lambda x: Unit.field_to_unit_space((x['x'], x['y'])), cells)

        self.cells = map(lambda x: (x[0] - pivot[0], x[1] - pivot[1]), self.cells)

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
        rotation += 6
        rotation %= 6
        answer = cell
        for i in range(rotation):
            answer = Unit.rot60(answer)

        return answer

class Position:
    pivot = (0, 0)
    rotation = 0 # ccw rotation

    def draw(self, unit, board):
        board.pivot = self.pivot
        for cell in unit.cells:
            rot = Unit.rotate(cell, self.rotation)
            shift = Unit.field_to_unit_space(self.pivot)
            shifted = (rot[0] + shift[0], rot[1] + shift[1])
            field = Unit.unit_to_field_space(shifted)
            board.unit[field[0], field[1]] = True


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
        pass

    def sym(self, x, y):
        if self.field[x, y]:
            return '#'

        is_pivot = (x, y) == self.pivot
        is_unit = self.unit[x, y]

        return self.syms[is_unit][is_pivot]

    def draw(self):
        for y in xrange(0, self.height):
            if y % 2:
                print '',

            for x in xrange(0, self.width):
                print self.sym(x, y),
            print

    syms = (('.', 'o'), ('*', '@'))

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f')

    args = parser.parse_args()

    input_data = json.load(open(args.file))

    board = Board(input_data['width'], input_data['height'], input_data['filled'])
    units = map(lambda x: Unit(x['members'], x['pivot']), input_data['units'])

    print input_data['units'][0]

    board.create_unit(units[0])
    pos = Position()
    pos.pivot = (5, 10)
    pos.rotation = -1

    pos.draw(units[0], board)
    board.draw()
    board.fix_unit()
