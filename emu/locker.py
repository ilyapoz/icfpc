#!/usr/bin/python
from emu import *
import phrases

import logging

class LockSearcher:
    def __init__(self, game):
        self.game = game

    def dfs(self, pos):
        self.marked.add((pos.pivot, pos.rotation))

        for phrase in phrases.all_sorted_lower:
            new_pos = Position(pos.unit, pos.pivot, pos.rotation)

            bad = False

            for letter in phrase[:-1]:
                new_pos = new_pos.apply_char(letter)
                move_res = self.game.try_pos(new_pos)

                if (   move_res == Game.MoveResult.Loss
                    or move_res == Game.MoveResult.Lock
                    or (new_pos.pivot, new_pos.rotation) in self.marked):
                    bad = True
                    break

            if bad: continue

            prev_pivot, prev_rotation = new_pos.pivot, new_pos.rotation

            new_pos = new_pos.apply_char(phrase[-1])
            move_res = self.game.try_pos(new_pos)

            if (   move_res == Game.MoveResult.Loss
                or (new_pos.pivot, new_pos.rotation) in self.marked):
                continue

            if move_res == Game.MoveResult.Lock:
                self.lock_state[(pos.pivot, pos.rotation)] = phrase
                continue

            self.marked.add((prev_pivot, prev_rotation))
            self.dfs(new_pos)
            self.back_move[(new_pos.pivot, new_pos.rotation)] = ((pos.pivot, pos.rotation), phrase)

    def find_lock_states(self):
        self.marked = set()
        self.lock_state = {}
        self.back_move = {}

        start_pos = self.game.cur_unit_pos()
        if start_pos is None:
            return

        self.dfs(start_pos)

        return (self.lock_state, self.back_move)
