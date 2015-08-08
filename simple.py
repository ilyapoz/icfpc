import sys
import json
import numpy

class Lock:
    def __init__(self, pos, moves):
        self.pos = pos
        self.moves = moves


class Board:
    def __init__(self, cfg):
        self.width = cfg['width']
        self.height = cfg['height']
        self.board = numpy.zeros((self.width, self.height), dtype=int)
        for cell_cfg in cfg['filled']:
            self.board[cell_cfg['x']][cell_cfg['y']] = 1

    def occupied(self, pos):
        return self.board[pos[0]][pos[1]] == 1

    def line_occupied(self, y):
        return all(self.occupied((x, y)) for x in range(0, self.width))

    def clear_line(self, y):
        # Move one line down
        for yy in range(y - 1, -1, -1):
            for x in range(0, self.width):
                self.board[x][yy + 1] = self.board[x][yy]
        for x in range(0, self.width):
            self.board[x][0] = 0

    def fill(self, pos):
        self.board[pos[0]][pos[1]] = 1

        y = self.height - 1
        lines_cleared = 0
        while y >= 0:
            occupied = self.line_occupied(y)
            if occupied:
                print 'Line cleared!'
                lines_cleared += 1
                self.clear_line(y)
            else:
                # Go to the next line
                y -= 1

        return lines_cleared

    def find_available_locks(self, pos):
        visited_positions = set()
        pos_to_lock = {}
        self.generate_positions_dfs(pos, '', visited_positions, pos_to_lock)
        return pos_to_lock.values()

    def east(self, pos):
        return pos[0] + 1, pos[1]

    def west(self, pos):
        return pos[0] - 1, pos[1]

    def south_east(self, pos):
        if pos[1] % 2 == 0:
            return pos[0], pos[1] + 1
        else:
            return pos[0] + 1, pos[1] + 1

    def south_west(self, pos):
        if pos[1] % 2 == 0:
            return pos[0] - 1, pos[1] + 1
        else:
            return pos[0], pos[1] + 1

    def get_start_pos(self):
        return (self.width - 1) / 2, 0

    def add_lock(self, pos, moves, pos_to_lock):
        if pos not in pos_to_lock:
            pos_to_lock[pos] = Lock(pos, moves)

    def generate_positions_dfs(self, pos, moves, visited_positions, pos_to_lock):
        if pos in visited_positions:
            return
        visited_positions.add(pos)

        #for move_info in [(self.east, 'b'), (self.west, 'p'), (self.south_east, 'm'), (self.south_west, 'g')]:
        for move_info in [(self.east, 'e'), (self.west, '!'), (self.south_east, 'o'), (self.south_west, 'a')]:
        #for move_info in [(self.east, 'E'), (self.west, 'W'), (self.south_east, 'SE'), (self.south_west, 'SW')]:
            new_pos = move_info[0](pos)
            if new_pos[0] < 0 or new_pos[0] >= self.width or new_pos[1] >= self.height or self.occupied(new_pos):
                self.add_lock(pos, moves + move_info[1], pos_to_lock)
            else:
                self.generate_positions_dfs(new_pos, moves + move_info[1], visited_positions, pos_to_lock)


def compute_points(unit_size, lines_cleared, lines_cleared_prev):
    points = unit_size + 100 * (1 + lines_cleared) * lines_cleared / 2
    line_bonus = (lines_cleared_prev - 1) * points / 10 if lines_cleared_prev > 1 else 0
    return points + line_bonus


def main():
    if len(sys.argv) != 3:
        print 'Usage: %s <input.json> <output.json>' % sys.argv[0]
        sys.exit(1)

    config = json.loads(open(sys.argv[1], 'r').read())
    assert len(config['units']) == 1
    assert len(config['units'][0]['members']) == 1
    assert len(config['sourceSeeds']) == 1 and config['sourceSeeds'][0] == 0

    solution = [{'problemId': config['id'], 'seed': config['sourceSeeds'][0], 'tag': 'simpleShit2', 'solution': ''}]

    board = Board(config)
    lines_cleared_prev = 0
    total_points = 0
    for i in range(config['sourceLength']):
        piece_pos = board.get_start_pos()
        assert not board.occupied(piece_pos)
        available_locks = board.find_available_locks(piece_pos)
        best_lock = max(available_locks, key=lambda l: l.pos[1])
        solution[0]['solution'] += best_lock.moves
        lines_cleared = board.fill(best_lock.pos)
        move_points = compute_points(1, lines_cleared, lines_cleared_prev)
        print 'Piece %d: %d points' % (i, move_points)
        lines_cleared_prev = lines_cleared
        total_points += move_points

    print 'Total points: %d' % total_points

    with open(sys.argv[2], 'w') as output_file:
        output_file.write(json.dumps(solution))

if __name__ == '__main__':
    main()