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

def norm(x, f = 10): return float(x) / (x + f)

def func(game, line_score, phrase_score):
    board = game.board()
    sum_y = 0

    for x in xrange(board.width):
        for y in xrange(board.height):
            if board.field[x, y] != 0: sum_y += y

#    holes = -factor.connected_components(1 - board.field)
    perim = -factor.perimeter(board.field) + line_score

    m_height = -factor.line_factors(board)[-1]

    hor = -factor.horiz_line_factor(board)

    return hor + 5 * norm(sum_y) + 3 * norm(line_score) + 2 * norm(perim)
    return 5 * norm(sum_y) + norm(line_score) + norm(perim, 50) + norm(m_height, 10)

def play(game, screen, game_index, game_count, silent):
    button_to_phrase = [(ord('1') + i, phrases.all[i]) for i in xrange(len(phrases.all))]
    phrase_legend = ', '.join(['%s for %s' % (chr(ph[0]), ph[1]) for ph in button_to_phrase])
    button_to_phrase_dict = dict(button_to_phrase)

    last_res = ''
    can_quit = False
    seq = ''

    while not can_quit:
        line_score = game.line_score()
        phrase_score = game.phrase_score()
        total_score = line_score + phrase_score

        if not silent:
            screen.addstr(1, 5, 'Game %2d out of %2d, unit %2d out of %2d' % \
                        (game_index + 1, game_count, game.current_state().unit_index + 1, len(game.units)))
            screen.addstr(2, 5, 'Score: %5d + %5d = %5d' % (line_score, phrase_score, total_score))
            screen.addstr(3, 5, 'Controls: W to go west, E to go east, A to go south west, D to go south east,')
            screen.addstr(4, 5, '          Q to turn ccw, R to turn clockwise, Z to cancel move, 0 to stop the current game.')
            screen.addstr(5, 5, '          %s' % phrase_legend)
            screen.addstr(6, 5, '          %s' % str(last_res))

            screen.addstr(8, 0, game.board().get_field_str(game.cur_unit_pos(), ext=0))

            screen.refresh()

        if seq == '':
            (lock_state, back_move) = locker.LockSearcher(game).find_lock_states()

            cur_pos = game.current_state().unit_pos
            cur_unit = cur_pos.unit

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

        key = ord('w')

        next_pos = None
        move_seq = None
        if not game.ended():
            if key in map(ord, ['w', 'W']):
                move_seq = 'p'
            elif key in map(ord, ['e', 'E']):
                move_seq = 'b'
            elif key in map(ord, ['a', 'A']):
                move_seq = 'g'
            elif key in map(ord, ['d', 'D']):
                move_seq = 'm'
            elif key in map(ord, ['q', 'Q']):
                move_seq = 's'
            elif key in map(ord, ['r', 'R']):
                move_seq = 'q'
            elif key in button_to_phrase_dict.keys():
                move_seq = button_to_phrase_dict[key]

        if key in map(ord, ['0']):
            can_quit = True
        elif key in map(ord, ['z', 'Z']):
            last_res = 'Undo'
            game.undo()
        elif move_seq is not None:
            move_seq = seq[0]
            seq = seq[1:]
            next_pos, last_res = game.try_commit_phrase(move_seq)
            if game.ended():
                 last_res += ' (Game over)'
                 break

        #screen.clear()

    return game.current_move_seq()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f')
    parser.add_argument('--output_file', '-o')
    parser.add_argument('--silent', action='store_true')

    args = parser.parse_args()

    config = json.load(open(args.file))

    try:
        screen = curses.initscr()
        curses.cbreak()

        results = []
        game_index = 0
        for game in emu.GameGenerator(config):
            moves = play(game, screen, game_index, len(config['sourceSeeds']), args.silent)
            game_index += 1
            results.append({
                'problemId': config['id'],
                'seed': game.unit_generator.source_seed,
                'solution': moves})
        json.dump(results, open(args.output_file, 'w'), indent=4)

    finally:
        curses.endwin()

if __name__ == '__main__':
#    main()
#    sys.exit()

    import cProfile, pstats, StringIO
    pr = cProfile.Profile()
    pr.enable()

    main()
    pr.disable()
    s = StringIO.StringIO()
    sortby = 'tottime'
    ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    ps.print_stats()
    print s.getvalue()
