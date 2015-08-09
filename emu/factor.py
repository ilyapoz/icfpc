#!/usr/bin/python

import emu

import numpy

class Stat:
    def __init__(self):
        self.vals = []

    def add(self, val):
        self.vals.append(val)

    def perc(self, q):
        s = sorted(self.vals)
        l = len(s)
        if not l:
            return [0 for x in q]
        return [s[(l-1) * x / 100] for x in q]

################################################
# Cell set factors
################################################

def perimeter(field):
    width, height = numpy.shape(field)
    answer = 0
    for x in range(width):
        for y in range(height):
            if field[x, y]:
                answer += 6

                for dx, dy in emu.Unit.shifts:
                    x_unit, y_unit = emu.Unit.field_to_unit_space((x, y))
                    xshifted = x_unit + dx
                    yshifted = y_unit + dy
                    xshifted, yshifted = emu.Unit.unit_to_field_space((xshifted, yshifted))

                    if not emu.Unit.in_field((xshifted, yshifted), field) or field[xshifted, yshifted]:
                        answer -= 1
    return answer

def connected_components(field, filled=True):
    visited = numpy.zeros(field.shape)
    print visited

################################################
# Board factors
################################################

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
    origin = emu.Unit.field_to_unit_space((board.width / 2, 0))
    for x in xrange(board.width):
        for y in xrange(board.height):
            if board.field[x, y]:
                unit_space = emu.Unit.field_to_unit_space((x, y))
                stat.add(emu.Unit.distance(origin, unit_space))

    return stat.perc([0, 25, 50, 100])


def board_factors(board):
    return line_factors(board) + distance_from_start(board) + [perimeter(board.field), connected_components(board.field)]

################################################
# Unit factors
################################################

def unit_perimeter(unit):
    extent = unit.extent()
    extent = (extent[0] + 5, extent[1] + 5)
    unit.calc_starting_position(extent[0])

    board = emu.Board(*extent)
    pos = emu.Position(unit)
    pos.pivot = unit.starting_position
    pos.rotation = 0

    pos = pos.south_west()
    board, dummy = board.fix_unit_and_clear(pos)
    return perimeter(board.field)

def unit_factors(unit):
    return [unit.symmetry_class, unit.perimeter]

################################################
# Game factors
################################################

def units_until_end(game):
    return len(game.units) - game.current_state().unit_index

def game_factors(game):
    return [units_until_end(game)]
