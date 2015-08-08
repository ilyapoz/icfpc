#!/usr/bin/python
import argparse
import numpy
import json
import sys
import os

class Unit:
    def __init__(self, cells, pivot):
        pivot = field_to_piece_space([pivot['x'], pivot['y'])
        
        self.cells = map(lambda x: [x['x'] - pivot['x'], x['y'] - pivot['y']], cells)
        self.rotation = 0

    def rotatecw(self):
        self.rotation = self.rotation - 1

    def rotateccw(self):
        self.rotation = self.rotation + 1

    def movesw(self):
        pass

    def movese(self):
        pass

    def draw(self, board, position):
        for x, y in self.cells:
            board

    @staticmethod
    def field_to_piece_space(coords):
        return [coords[0], ]

    @staticmethod
    def piece_to_field_space(coords):
        return []

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f')

    args = parser.parse_args()

    input_data = json.load(open(args.file))

    board = Board(input_data['width'], input_data['height'], input_data['filled'])
    units = map(lambda x: Unit(x['members'], x['pivot']), input_data['units'])
    board.create_unit(units[0])
    board.draw()
    board.fix_unit()
