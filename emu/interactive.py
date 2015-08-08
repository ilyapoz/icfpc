#!/usr/bin/python
import emu
import argparse
import json
import curses


def play(game, screen):
    stop_game = False
    while not game.ended() and not stop_game:
        screen.addstr(1, 5, 'Score: %d' % game.score())
        screen.addstr(3, 5, 'Controls: W to go west, E to go east, S to go south west, D to go south east,')
        screen.addstr(4, 5, '          Q to turn ccw, R to turn clockwise, Z to cancel move, Backspace to quit.')

        game.cur_position.draw(game.board)
        screen.addstr(6, 0, game.board.get_field_str(ext=1))
        screen.refresh()

        key = screen.getch()
        move_result = None
        if key == ord('w') or key == ord('W'):
            move_result = game.try_west()
        elif key == ord('e') or key == ord('E'):
            move_result = game.try_east()
        elif key == ord('s') or key == ord('S'):
            move_result = game.try_south_west()
        elif key == ord('d') or key == ord('D'):
            move_result = game.try_south_east()
        elif key == ord('q') or key == ord('Q'):
            move_result = game.try_ccw()
        elif key == ord('r') or key == ord('R'):
            move_result = game.try_cw()

        screen.clear()
        screen.addstr(5, 5, 'You have entered %d' % key)

        if key == curses.KEY_BACKSPACE:
            stop_game = True

    return ''


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
        for game in emu.GameGenerator(config):
            moves = play(game, screen)
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
