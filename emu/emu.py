#!/usr/bin/python
import argparse
import numpy
import json
import sys
import os
import unittest
import math
import logging
import phrases
import factor

logging.basicConfig(filename='emu.log', level=logging.DEBUG)

class Unit:
    def __init__(self, cells, pivot):
        pivot = Unit.field_to_unit_space((pivot['x'], pivot['y']))

        self.cells = map(lambda x: Unit.field_to_unit_space((x['x'], x['y'])), cells)

        self.cells = map(lambda x: (x[0] - pivot[0], x[1] - pivot[1]), self.cells)
        self.symmetry_class = self.calc_symmetry_class()
        self.perimeter = factor.unit_perimeter(self)

    shifts = (
        (1, 0),
        (0, 1),
        (-1, 1),
        (-1, 0),
        (0, -1),
        (1, -1),
    )

    @staticmethod
    def in_field(cell, field):
        width, height = numpy.shape(field)
        return 0 <= cell[0] < width and 0 <= cell[1] < height

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
    def distance(cell1, cell2):
        x = cell2[0] - cell1[0]
        y = cell2[1] - cell1[1]
        z = -(x + y)
        return (abs(x) + abs(y) + abs(z)) / 2

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

    def apply_char(self, c):
        if c in {'p', "'", '!', '.', '0', '3'}: return self.west()
        if c in {'b', 'c', 'e', 'f', 'y', '2'}: return self.east()
        if c in {'a', 'g', 'h', 'i', 'j', '4'}: return self.south_west()
        if c in {'l', 'm', 'n', 'o', ' ', '5'}: return self.south_east()
        if c in {'d', 'q', 'r', 'v', 'z', '1'}: return self.cw()
        if c in {'k', 's', 't', 'u', 'w', 'x'}: return self.ccw()
        if c in {"\t", "\n", "\r"}: pass

        assert False


class Board:
    def __init__(self, width, height, filled=None, field=None):
        self.width = width
        self.height = height
        self.field = numpy.zeros((width, height), int) if field is None else numpy.copy(field)
        if filled is not None:
            for cell in filled:
                self.field[cell['x'], cell['y']] = 1

    def in_board(self, cell):
        return Unit.in_field(cell, self.field)

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

    def phrase_score(self):
        phrase_counts = [0] * len(phrases.all)
        moves = self.current_move_seq().lower()
        for index, phrase in enumerate(phrases.all):
            pos = -1
            while True:
                pos = moves.find(phrase.lower(), pos + 1)
                if pos == -1:
                    break
                phrase_counts[index] += 1

        phrase_points = 0
        for i in xrange(len(phrases.all)):
            if phrase_counts[i] != 0:
                phrase_points += 2 * len(phrases.all[i]) * phrase_counts[i] + 300

        return phrase_points

    class State:
        def __init__(self, unit_index, unit_pos, board, line_score, visited_positions, lines_cleared_prev, move_chr):
            self.unit_index = unit_index
            self.unit_pos = unit_pos
            self.board = board
            self.line_score = line_score
            self.visited_positions = visited_positions
            self.lines_cleared_prev = lines_cleared_prev
            self.move_chr = move_chr

    def __init__(self, board, unit_generator):
        self.unit_generator = unit_generator
        self.units = list(unit_generator)
        self.game_ended = False
        self.state_stack = []
        self.switch_to_next_unit(board, 0, 0, '')

    def current_move_seq(self):
        return ''.join([s.move_chr for s in self.state_stack])

    def switch_to_next_unit(self, board, line_score, lines_cleared, move_chr):
        cur_unit_index = -1 if len(self.state_stack) == 0 else self.current_state().unit_index
        next_unit_index = cur_unit_index + 1

        logging.debug('switch_to_next_unit, cur_index=%d, next_index=%d, unit_count=%d' % (cur_unit_index, next_unit_index, len(self.units)))

        if next_unit_index == len(self.units):
            self.game_ended = True
            logging.debug('Game ended because no more pieces are available')

            # Add a state even if there are no more pieces (so that the board drawing will be updated)
            self.state_stack.append(Game.State(cur_unit_index, None, board, line_score, None, None, move_chr))

            return

        next_unit = self.units[next_unit_index]
        next_unit_pos = Position(next_unit, next_unit.starting_position, 0)

        if next_unit_index == 0 or self.try_pos_impl(next_unit_pos, board, None) == Game.MoveResult.Continue:
            logging.debug('Piece %d started' % next_unit_index)
        else:
            self.game_ended = True
            logging.debug('Game ended because piece %d cannot be placed' % next_unit_index)

        # Add a state even if a unit cannot be added (so that the board drawing will be updated)
        self.state_stack.append(Game.State(
            next_unit_index,
            next_unit_pos,
            board,
            line_score,
            PersistentStack(tail=(next_unit_pos.pivot[0], next_unit_pos.pivot[1], next_unit_pos.rotation)),
            lines_cleared,
            move_chr))

    def ended(self):
        return self.game_ended

    def current_state(self):
        return self.state_stack[-1]

    def line_score(self):
        return self.current_state().line_score

    def cur_unit_pos(self):
        return None if self.ended() else self.current_state().unit_pos

    def board(self):
        return self.current_state().board

    def commit_pos(self, pos, move_chr):
        assert not self.ended()

        move_result = self.try_pos(pos)
        assert move_result != Game.MoveResult.Loss

        if move_result == Game.MoveResult.Lock:
            logging.debug('Piece locked')
            (new_board, lines_cleared) = self.board().fix_unit_and_clear(self.cur_unit_pos())
            logging.debug('Lines cleared: %d, prev lines cleared: %d' % (lines_cleared, self.current_state().lines_cleared_prev))
            move_score = Game.compute_points(len(self.cur_unit_pos().unit.cells), lines_cleared, self.current_state().lines_cleared_prev)
            logging.debug('Prev score: %d, move score: %d' % (self.line_score(), move_score))
            self.switch_to_next_unit(new_board, self.line_score() + move_score, lines_cleared, move_chr)
        elif move_result == Game.MoveResult.Continue:
            self.state_stack.append(Game.State(
                self.current_state().unit_index,
                pos,
                self.current_state().board,
                self.current_state().line_score,
                self.current_state().visited_positions.push((pos.pivot[0], pos.pivot[1], pos.rotation)),
                self.current_state().lines_cleared_prev,
                move_chr))
        else:
            logging.debug(move_result)
            assert False

    def try_pos(self, pos):
        return self.try_pos_impl(pos, self.board(), self.current_state().visited_positions.items())

    def try_pos_impl(self, pos, board, visited_positions):
        if visited_positions is not None and (pos.pivot[0], pos.pivot[1], pos.rotation) in visited_positions:
            return Game.MoveResult.Loss

        for x, y in pos.field_space():
            if not board.in_board((x, y)) or board.field[x, y]:
                return Game.MoveResult.Lock

        return Game.MoveResult.Continue

    def undo(self, steps=1):
        if self.game_ended:
            self.game_ended = False
        for i in range(steps):
            if len(self.state_stack) > 1:
                self.state_stack.pop()

    def try_commit_phrase(self, phrase):
        assert len(phrase) > 0
        phrase = phrase.lower()

        next_pos = None
        for i, c in enumerate(phrase):
            if self.ended():
                return None, Game.MoveResult.Loss
            next_pos = self.cur_unit_pos().apply_char(c)

            res = self.try_pos(next_pos)
            if res == Game.MoveResult.Loss:
                return None, res

            self.commit_pos(next_pos, c)
            if res == Game.MoveResult.Lock:
                return next_pos, res

        return next_pos, Game.MoveResult.Continue


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
    pos.rotation = 1

    pos = pos.south_west()

    board, dummy = board.fix_unit_and_clear(pos)
    board.draw_field(pos)
    print factor.board_factors(board)

    print factor.unit_factors(unit)
