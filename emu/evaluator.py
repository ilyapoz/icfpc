#!/usr/bin/python
import emu
import locker

import argparse
import json
import logging
import sys
import factor
import math
import threading

sys.path.append('/Users/hr0nix/icfpc/icfpc')
import bayes_opt

class Evaluator:
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
            #print seq

    @staticmethod
    def evaluate(configs, score_func):

        thread_scores = [0] * len(configs)
        threads = []

        for i in xrange(len(configs)):

            def thread_func(index):
                total_score = 0

                for game in emu.GameGenerator(configs[index]):
                    Evaluator.play(game, score_func)

                    cur_score = game.line_score() + game.phrase_score()
                    total_score += cur_score

                average_score = total_score // len(configs[index]['sourceSeeds'])
                thread_scores[index] = average_score

            thread = threading.Thread(target=thread_func, args=(i,))
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

        overall_average_score = sum(thread_scores) // len(thread_scores)

        print
        print 'Overall average score is %d' % overall_average_score
        print 'Thread scores: %s' % thread_scores
        print

        return overall_average_score


def inner(arr1, arr2):
    assert len(arr1) == len(arr2)
    return sum([arr1[i] * arr2[i] for i in xrange(len(arr1))])

def normalize(arr):
    s = sum(arr)
    return [x / s for x in arr]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--files', '-f', nargs='+')
    #parser.add_argument('--output_file', '-o')

    args = parser.parse_args()
    configs = [json.load(open(f)) for f in args.files]

    def objective(w_holes, w_horiz_lines, w_dist_sum, w_perimeter, w_line_score, w_phrase_score):
        factor_weights = [w_holes, w_horiz_lines, w_dist_sum, w_perimeter, w_line_score, w_phrase_score]

        def score_func(game, line_score, phrase_score):
            board = game.board()
            holes = factor.connected_components(1 - board.field)
            factors = [holes / (holes + 10.0),
                       factor.horiz_line_factor(board),
                       factor.mean_distance_sum(board),
                       factor.perimeter(board.field),
                       line_score,
                       phrase_score]

            #print factors

            #cur_or_next_unit_index = game.current_state().unit_index
            #if cur_or_next_unit_index < len(game.units) - 1:
            #    cur_or_next_unit_index += 1
            #cur_or_next_unit = game.units[cur_or_next_unit_index]
            #unit_factors = factor.unit_factors(cur_or_next_unit)

            return inner(factor_weights, factors)

        print 'Evaluating...'
        score = Evaluator.evaluate(configs, score_func)
        print 'Evaluation result: %f' % score

        return math.log(score)

    optimizer = bayes_opt.BayesianOptimization(
        objective,
        {
            'w_holes': [-10.0, 0.0],
            'w_horiz_lines': [-10.0, 0.0],
            'w_dist_sum': [0.0, 10.0],
            'w_perimeter': [-0.1, 0.1],
            'w_line_score': [0.0, 10.0],
            'w_phrase_score': [0.0, 10.0]
        })

    optimizer.explore(
    {
        'w_holes': [0.0],
        'w_horiz_lines': [-3.0],
        'w_dist_sum': [2.0],
        'w_perimeter': [-0.01],
        'w_line_score': [5.0],
        'w_phrase_score': [5.0]
    })

    optimizer.maximize(n_iter=100, acq='ucb')

    print 'Max objective found: %s' % optimizer.res['max']

if __name__ == '__main__':
    main()
