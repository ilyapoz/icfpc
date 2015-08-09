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

                for xshifted, yshifted in emu.Unit.neighbors((x, y)):
                    if not emu.Unit.in_field((xshifted, yshifted), field) or field[xshifted, yshifted]:
                        answer -= 1
    return float(answer) / (width + height)

def connected_components(field):
    visited = numpy.zeros(field.shape)
    width, height = field.shape

    def find_unvisited():
        for x in range(width):
            for y in range(height):
                if emu.Unit.in_field((x, y), field) and field[x, y] and not visited[x, y]:
                    return (x, y)

    def discover(cell):
        level = [cell]
        visited[level[0]] = 1

        while level:
            next_level=[]

            for cell in level:
                for x, y in emu.Unit.neighbors(cell):
                    if emu.Unit.in_field((x, y), field) and field[x, y] and not visited[x, y]:
                        visited[x, y] = 1
                        next_level.append((x, y))

            level = next_level

    answer = 0
    while True:
        x = find_unvisited()
        if x is None:
            return answer

        answer += 1
        discover(x)

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


def mean_distance_sum(board):
    dist_sum = 0.0
    dist_count = 0
    origin = emu.Unit.field_to_unit_space((board.width / 2, 0))
    for x in xrange(board.width):
        for y in xrange(board.height):
            if board.field[x, y]:
                unit_space = emu.Unit.field_to_unit_space((x, y))
                dist = emu.Unit.distance(origin, unit_space)
                dist_sum += dist
                dist_count += 1

    mean_dist = 0.0 if dist_count == 0 else dist_sum / dist_count
    return mean_dist / (board.width + board.height)


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
