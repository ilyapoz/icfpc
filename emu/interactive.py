import emu
import argparse
import json
import curses


def play(game, screen):
    stop_game = False
    while not game.ended() and not stop_game:
        screen.addstr(1, 5, 'Score: %d' % game.score())
        screen.addstr(3, 5, 'Controls: W to go west, E to go east, S to go south west, D to go south east,')
        screen.addstr(4, 5, '          Z to cancel move, Q to quit.')

        screen.addstr(6, 0, game.board.get_field_str(ext=1))
        screen.refresh()

        key = screen.getch()

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

        board_generator = lambda: emu.Board(config['width'], config['height'], config['filled'])
        results = []
        for game in emu.GameGenerator(board_generator, config['units'], config['sourceSeeds'], config['sourceLength']):
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