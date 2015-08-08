#!/usr/bin/python
import emu
import argparse
import json
import curses


def play(game, screen):
    while not game.ended():
        screen.addstr(1, 5, 'Score: %d' % game.score())
        screen.addstr(3, 5, 'Controls: W to go west, E to go east, S to go south west, D to go south east,')
        screen.addstr(4, 5, '          Q to turn ccw, R to turn clockwise, Z to cancel move, Ctr+C to quit.')

        screen.addstr(6, 0, game.board.get_field_str(ext=0))
        screen.refresh()

        key = screen.getch()

        next_pos = None
        if key == ord('w') or key == ord('W'):
            next_pos = game.cur_position.west()
        elif key == ord('e') or key == ord('E'):
            next_pos = game.cur_position.east()
        elif key == ord('s') or key == ord('S'):
            next_pos = game.cur_position.south_west()
        elif key == ord('d') or key == ord('D'):
            next_pos = game.cur_position.south_east()
        elif key == ord('q') or key == ord('Q'):
            next_pos = game.cur_position.ccw()
        elif key == ord('r') or key == ord('R'):
            next_pos = game.cur_position.cw()

        if next_pos != None:
            move_result = game.try_pos(next_pos)
            if move_result != emu.Game.MoveResult.Loss:
                game.commit_pos(next_pos)

        screen.clear()
        screen.addstr(5, 5, 'You have entered %d' % key)

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
