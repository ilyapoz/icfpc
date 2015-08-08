import emu
import argparse
import json
import curses


def play(game, screen):
    stop_game = False
    while not game.ended() and not stop_game:
        screen.addstr(1, 5, 'Score: %d' % game.score())
        screen.addstr(3, 5, 'Controls: W to go west, E to go east, S to go south west, D to go south east,')
        screen.addstr(4, 5, '          Q to turn ccw, R to turn clockwise, Z to cancel move, Q to quit.')

        game.cur_position.draw(game.board)
        screen.addstr(6, 0, game.board.get_field_str(ext=1))
        screen.refresh()

        key = screen.getch()
        if key == 'w' or key == 'W':
            game.try_west()
        elif key == 'e' or key == 'E':
            game.try_east()

        screen.clear()
        screen.addstr(5, 5, 'You have entered %d' % key)

        if key == ord('q'):
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