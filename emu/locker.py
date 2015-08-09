#!/usr/bin/python
from emu import *
import logging

class LockSearcher:
    def __init__(self, game):
        self.game = game

    def dfs(self, pos):

        self.marked.add((pos.pivot, pos.rotation))

        for move, letter in [
            (Position.south_west, 'a'),
            (Position.south_east, 'l'),
            (Position.west, 'p'),
            (Position.east, 'b'),
            (Position.cw, 'd'),
            (Position.ccw, 'k')
        ]:
            new_pos = move(pos)
            if (new_pos.pivot, new_pos.rotation) in self.marked: continue

            move_res = self.game.try_pos(new_pos)
            if move_res == Game.MoveResult.Loss: continue

            if move_res == Game.MoveResult.Lock:
                self.locked[(pos.pivot, pos.rotation)] = letter
                continue

            self.dfs(new_pos)
            self.back_move[(new_pos.pivot, new_pos.rotation)] = ((pos.pivot, pos.rotation), letter)

    def get_lowest_y(self, coords):
        cur_unit = self.game.current_state().unit_pos.unit
        pos = Position(cur_unit, coords[0][0], coords[0][1])

        return sum(cell[1] for cell in pos.field_space())

    def find_lock_states(self):
        self.marked = set()
        self.locked = {}
        self.back_move = {}

        start_pos = self.game.cur_unit_pos()
        if start_pos is None:
            return

        self.dfs(start_pos)

        l = [(key, val) for key, val in self.locked.iteritems()]

        lowest_pos, lowest_y = l[0], self.get_lowest_y(l[0])

        for pos in l:
            pos_y = self.get_lowest_y(pos)
            if pos_y > lowest_y:
                lowest_pos, lowest_y = pos, pos_y

        seq = ''

        while lowest_pos is not None:
            seq = lowest_pos[1] + seq
            lowest_pos = self.back_move.get(lowest_pos[0])

        return seq
