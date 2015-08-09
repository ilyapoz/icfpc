#!/usr/bin/python
import emu
import argparse
import json
import curses


def play(game, screen, game_index, game_count):
    last_res = ''
    can_quit = False
    while not can_quit:
        screen.addstr(1, 5, 'Game %d out of %d, unit %d out of %d' % \
                      (game_index + 1, game_count, game.current_state().unit_index + 1, len(game.units)))
        screen.addstr(2, 5, 'Score: %d' % game.score())
        screen.addstr(3, 5, 'Controls: W to go west, E to go east, A to go south west, D to go south east,')
        screen.addstr(4, 5, '          Q to turn ccw, R to turn clockwise, Z to cancel move, 0 to stop the current game.')
        screen.addstr(5, 5, '          %s' % str(last_res))

        screen.addstr(7, 0, game.board().get_field_str(game.cur_unit_pos(), ext=0))
        screen.refresh()

        key = screen.getch()

        next_pos = None
        move_chr = None
        if not game.ended():
            if key in map(ord, ['w', 'W']):
                move_chr = 'p'
            elif key in map(ord, ['e', 'E']):
                move_chr = 'b'
            elif key in map(ord, ['a', 'A']):
                move_chr = 'g'
            elif key in map(ord, ['d', 'D']):
                move_chr = 'm'
            elif key in map(ord, ['q', 'Q']):
                move_chr = 's'
            elif key in map(ord, ['r', 'R']):
                move_chr = 'q'

            if move_chr is not None:
                next_pos = game.cur_unit_pos().apply_char(move_chr)

        if key in map(ord, ['0']):
            can_quit = True
        elif key in map(ord, ['z', 'Z']):
            last_res = 'Undo'
            game.undo()

        if next_pos is not None:
            move_result = game.try_pos(next_pos)
            last_res = move_result
            if move_result != emu.Game.MoveResult.Loss:
                game.commit_pos(next_pos, move_chr)
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
        json.dump(results, open(args.output_file, 'w'))

    finally:
        curses.endwin()

if __name__ == '__main__':
    main()
