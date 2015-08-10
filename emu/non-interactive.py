#!/usr/bin/python
import factor
import emu
import phrases
import locker

import argparse
import json
import curses
import logging
import sys

def func(game, line_score, phrase_score):
    board = game.board()

    res = 0

    for x in xrange(board.width):
        for y in xrange(board.height):
            if board.field[x, y] != 0:
                res += y

    return res + line_score * 100

def play(game, screen, game_index, game_count, silent):
    button_to_phrase = [(ord('1') + i, phrases.all[i]) for i in xrange(len(phrases.all))]
    phrase_legend = ', '.join(['%s for %s' % (chr(ph[0]), ph[1]) for ph in button_to_phrase])

    seq = ''

    while True:
        line_score = game.line_score()
        phrase_score = game.phrase_score()
        total_score = line_score + phrase_score

        if not silent:
            screen.addstr(1, 5, 'Game %d out of %d, unit %d out of %d' % \
                          (game_index + 1, game_count, game.current_state().unit_index + 1, len(game.units)))
            screen.addstr(2, 5, 'Score: %6d + %6d = %6d' % (line_score, phrase_score, total_score))
            screen.addstr(3, 5, 'Controls: W to go west, E to go east, A to go south west, D to go south east,')
            screen.addstr(4, 5, '          Q to turn ccw, R to turn clockwise, Z to cancel move, 0 to stop the current game.')
            screen.addstr(5, 5, '          %s' % phrase_legend)

            screen.addstr(8, 0, game.board().get_field_str(game.cur_unit_pos(), ext=0))

            screen.refresh()

        if seq == '':
            (lock_state, back_move) = locker.LockSearcher(game).find_lock_states()

            cur_pos = game.current_state().unit_pos
            cur_unit = cur_pos.unit

            best_lock_state, best_lock_score = None, 0

            for state, lock_phrase in lock_state.iteritems():
                line_score = -game.line_score()
                phrase_score = 0

                undo_times = 1
                pos_before_lock = emu.Position(cur_unit, state[0], state[1])

                for letter in lock_phrase[:-1]:
                    pos_before_lock = pos_before_lock.apply_char(letter)

                if ((cur_pos.pivot, cur_pos.rotation) !=
                    (pos_before_lock.pivot, pos_before_lock.rotation)):
                    game.commit_pos(pos_before_lock, '?')
                    undo_times += 1

                lock_pos = pos_before_lock.apply_char(lock_phrase[-1])
                game.commit_pos(lock_pos, lock_phrase[-1])

                line_score += game.line_score()
                position_score = func(game, line_score, phrase_score)

                game.undo(undo_times)

                if (   best_lock_state is None
                    or best_lock_score < position_score):
                    best_lock_state = state
                    best_lock_score = position_score

            cur_state = (best_lock_state, lock_state[best_lock_state])

            while cur_state is not None:
                seq = cur_state[1] + seq
                cur_state = back_move.get(cur_state[0])

        _, move_res = game.try_commit_phrase(seq[0])

        if move_res == emu.Game.MoveResult.Loss:
            #logging.debug('ERRRRRRRRRRORRRRRRRROOORORORO !!!!!!!!')
            seq = ''
            continue

        seq = seq[1:]

        if game.ended():
            break

        #screen.clear()

    return game.current_move_seq()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f', required=True)
    parser.add_argument('--output_file', '-o')
    parser.add_argument('-t', type=int)
    parser.add_argument('-m', type=int)
    parser.add_argument('-c', type=int)
    parser.add_argument('-p', action='append')

    parser.add_argument('--verbose', action='store_true')

    args = parser.parse_args()

    if args.p:
        phrases.all = args.p

    config = json.load(open(args.file))

    try:
        if args.verbose:
            screen = curses.initscr()
            curses.cbreak()
        else:
            screen = []

        results = []
        game_index = 0
        for game in emu.GameGenerator(config):
            moves = play(game, screen, game_index, len(config['sourceSeeds']), not args.verbose)
            game_index += 1
            results.append({
                'problemId': config['id'],
                'seed': game.unit_generator.source_seed,
                'solution': moves})

        json.dump(results, open(args.output_file, 'w') if args.output_file else sys.stdout, indent=4)

    finally:
        if args.verbose:
            curses.endwin()

if __name__ == '__main__':
    main()
