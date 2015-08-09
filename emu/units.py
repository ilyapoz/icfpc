#!/usr/bin/python
from emu import *

parser = argparse.ArgumentParser()
parser.add_argument('--file', '-f')

args = parser.parse_args()

input_data = json.load(open(args.file))

units = map(lambda x: Unit(x['members'], x['pivot']), input_data['units'])
extent = (0, 0)
for u in units:
    u_ext = u.extent()
    extent = (max(extent[0], u_ext[0]), max(extent[1], u_ext[1]))

board = Board(extent[0] * 2, extent[1] * 2, [])

for u in units:
    u.calc_starting_position(board.width)

for i in range(len(units)):
    print 'Unit %d (symmetry %d)' % (i, units[i].symmetry_class)
    pos = Position(units[i])
    pos.rotation = 0

    pos.pivot = units[i].starting_position
    board.draw_field(pos)
    print ''
