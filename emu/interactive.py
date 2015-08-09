#!/usr/bin/python
import emu
import phrases

import argparse
import json
import curses


def play(game, screen, game_index, game_count):
    button_to_phrase = [(ord('1') + i, phrases.all[i]) for i in xrange(len(phrases.all))]
    phrase_legend = ', '.join(['%s for %s' % (chr(ph[0]), ph[1]) for ph in button_to_phrase])
    button_to_phrase_dict = dict(button_to_phrase)

    last_res = ''
    can_quit = False
    while not can_quit:
        line_score = game.line_score()
        phrase_score = game.phrase_score()
        total_score = line_score + phrase_score

        screen.addstr(1, 5, 'Game %d out of %d, unit %d out of %d' % \
                      (game_index + 1, game_count, game.current_state().unit_index + 1, len(game.units)))
        screen.addstr(2, 5, 'Score: %d + %d = %d' % (line_score, phrase_score, total_score))
        screen.addstr(3, 5, 'Controls: W to go west, E to go east, A to go south west, D to go south east,')
        screen.addstr(4, 5, '          Q to turn ccw, R to turn clockwise, Z to cancel move, 0 to stop the current game.')
        screen.addstr(5, 5, '          %s' % phrase_legend)
        screen.addstr(6, 5, '          %s' % str(last_res))

        screen.addstr(8, 0, game.board().get_field_str(game.cur_unit_pos(), ext=0))
        screen.refresh()

        key = screen.getch()

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
            next_pos, last_res = game.try_commit_phrase(move_seq)
            if game.ended():
                last_res += ' (Game over)'

        screen.clear()

    return game.current_move_seq()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f')
    parser.add_argument('--output_file', '-o')

    args = parser.parse_args()

    config = json.load(open(args.file))

    try:
        screen = curses.initscr()
        curses.cbreak()

        results = []
        game_index = 0
        for game in emu.GameGenerator(config):
            moves = play(game, screen, game_index, len(config['sourceSeeds']))
            game_index += 1
            results.append({
                'problemId': config['id'],
                'seed': game.unit_generator.source_seed,
                'tag': 'interactive',
                'solution': moves})
        json.dump(results, open(args.output_file, 'w'), indent=4)

    finally:
        curses.endwin()

if __name__ == '__main__':
    main()
