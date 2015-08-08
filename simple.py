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
        return self.board[pos[0]][pos[1]] == 0

    def line_occupied(self, y):
        return all(self.occupied(x, y) for x in range(0, self.width))

    def flush_line(self, y):
        # Move one line down
        for yy in range(y).reverse():
            for x in range(0, self.width):
                self.board[x][yy + 1] = self.board[x][yy]
        for x in range(0, self.width):
            self.board[x][0] = 0

    def fill(self, pos):
        self.board[pos[0]][pos[1]] = 1

        y = self.height - 1
        while y >= 0:
            line_occupied = self.line_occupied(y)
            if line_occupied:
                self.flush_line(y)
            else:
                # Go to the next line
                y += 1

    def find_available_locks(self, pos):
        visited_positions = set()
        pos_to_lock = {}
        self.generate_positions_dfs(pos, '', visited_positions, pos_to_lock)
        return pos_to_lock.values

    def east(self, pos):
        return pos[0] - 1, pos[1]

    def west(self, pos):
        return pos[0] + 1, pos[1]

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
        return self.width / 2, 0

    def add_lock(self, pos, moves, pos_to_lock):
        if pos not in pos_to_lock:
            pos_to_lock[pos] = Lock(pos, moves)

    def generate_positions_dfs(self, pos, moves, visited_positions, pos_to_lock):
        if pos in visited_positions:
            return
        visited_positions.add(pos)

        for move_info in [(self.east, ''), (self.west, ''), (self.south_east, ''), (self.south_west, '')]:
            new_pos = move_info[0](pos)
            if new_pos[0] < 0 or new_pos[0] >= self.width or new_pos[1] >= self.height or self.occupied(new_pos):
                self.add_lock(pos, moves + move_info[1], pos_to_lock)
            else:
                self.generate_positions_dfs(new_pos, moves + move_info[1], visited_positions, pos_to_lock)

def main():
    if len(sys.argv) != 2:
        print 'Usage: %s <file.json>' % sys.argv[0]
        sys.exit(1)

    config = json.loads(open(sys.argv[1], 'r').read())
    assert len(config['units']) == 1
    assert len(config['units'][0]['members']) == 1
    assert len(config['sourceSeeds']) == 1 and config['sourceSeeds'][0] == 0

    solution = [{'problemId': '1', 'seed': config['sourceSeeds'], 'tag': 'simpleShit', 'solution': ''}]

    board = Board(config)
    for i in range(config['sourceLength']):
        piece_pos = board.get_start_pos()
        assert not board.occupied(piece_pos)
        available_locks = board.find_available_locks(piece_pos)
        best_lock = max(available_locks, key=lambda l: l.pos.y)
        solution['solution'] += best_lock.moves
        board.fill(best_lock.pos)

    print json.dumps(solution)

if __name__ == '__main__':
    main()