#!/usr/bin/python
from emu import *

parser = argparse.ArgumentParser()
parser.add_argument('--file', '-f')

args = parser.parse_args()

input_data = json.load(open(args.file))

board = Board(input_data['width'], input_data['height'], input_data['filled'])
units = map(lambda x: Unit(x['members'], x['pivot']), input_data['units'])

board.draw_field()
