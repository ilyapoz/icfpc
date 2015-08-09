#!/usr/bin/python

from emu import *
import numpy

class Stat:
    def __init__(self):
        self.vals = []

    def add(self, val):
        self.vals.append(val)

    def perc(self, q):
        s = sorted(self.vals)
        l = len(s)
        return [s[(l-1) * x / 100] for x in q]

def line_factors(board):
    stat = Stat()
    for col in xrange(board.width):
        for row in xrange(board.height):
            if board.field[col, row] == 1:
                stat.add(board.height - row)
                break
        else:
            stat.add(0)

    return stat.perc([0, 25, 50, 75, 100])


def distance_from_start(board):
    stat = Stat()
    origin = Unit.field_to_unit_space((board.width / 2, 0))
    for x in xrange(board.width):
        for y in xrange(board.height):
            if board.field[x, y]:
                unit_space = Unit.field_to_unit_space((x, y))
                stat.add(Unit.distance(origin, unit_space))

    return stat.perc([0, 25, 50, 100])


def board_factors(board):
    #return line_factors(board) + distance_from_start(board)
    return distance_from_start(board)
