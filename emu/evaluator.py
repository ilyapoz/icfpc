import emu
import locker

import argparse
import json
import logging

class Evaluator:
#    @staticmethod
#    def func(game, line_score, phrase_score, pos_before_lock):
#        if line_score >= 100: return 1e10
#        return sum(cell[1] for cell in pos_before_lock.field_space())

    @staticmethod
    def play(game, score_func):
        while not game.ended():
            cur_pos = game.current_state().unit_pos
            cur_unit = cur_pos.unit
            (lock_state, back_move) = locker.LockSearcher(game).find_lock_states()

            best_lock_state, best_lock_score = None, 0

            for state, letter in lock_state.iteritems():
                line_score = -game.line_score()
                phrase_score = 0

                undo_times = 1
                pos_before_lock = emu.Position(cur_unit, state[0], state[1])

                if ((cur_pos.pivot, cur_pos.rotation) !=
                    (pos_before_lock.pivot, pos_before_lock.rotation)):
                    game.commit_pos(pos_before_lock, '?')
                    undo_times += 1

                lock_pos = pos_before_lock.apply_char(letter)
                game.commit_pos(lock_pos, letter)

                line_score += game.line_score()
                position_score = score_func(game, line_score, phrase_score)

                game.undo(undo_times)

                if (   best_lock_state is None
                    or best_lock_score < position_score):
                    best_lock_state = state
                    best_lock_score = position_score

            seq = ''
            cur_state = (best_lock_state, lock_state[best_lock_state])

            while cur_state is not None:
                seq = cur_state[1] + seq
                cur_state = back_move.get(cur_state[0])

            game.try_commit_phrase(seq)
            print seq

    @staticmethod
    def evaluate(config, score_func):
        if len(config['sourceSeeds']) == 0: return 0.0

        max_score, min_score = 0, 1e100
        total_score = 0

        for game in emu.GameGenerator(config):
            Evaluator.play(game, score_func)

            cur_score = game.line_score() + game.phrase_score()
            total_score += cur_score

            min_score = min(min_score, cur_score)
            max_score = max(max_score, cur_score)

        average_score = total_score // len(config['sourceSeeds'])

        print 'Board #%d:' % config['id']
        print '  min / max score: %d / %d' % (min_score, max_score)
        print '  average score: %d' % int(average_score)

        return average_score

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f')
    parser.add_argument('--output_file', '-o')

    args = parser.parse_args()
    config = json.load(open(args.file))

    #Evaluator.evaluate(config, Evaluator.func)

if __name__ == '__main__':
    main()
