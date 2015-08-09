#!/usr/bin/python

import factor
import emu
import argparse
import json


def play(game, solution_config):
    _, outcome = game.try_commit_phrase(solution_config['solution'], stop_on_lock=False)
    if outcome == emu.Game.MoveResult.Loss:
        print 'Game with seed %d: LOSS' % solution_config['seed']
    else:
        line_score = game.line_score()
        phrase_score = game.phrase_score()
        total_score = line_score + phrase_score
        end_marker = '' if game.ended() else '[NOT ENDED]'
        print 'Game with seed %d: %d + %d = %d points %s' % \
              (solution_config['seed'], line_score, phrase_score, total_score, end_marker)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f')
    parser.add_argument('--solution_file', '-o')

    args = parser.parse_args()

    game_config = json.load(open(args.file))
    solution_config = json.load(open(args.solution_file))

    assert len(game_config['sourceSeeds']) == len(solution_config)

    game_index = 0
    for game in emu.GameGenerator(game_config):
        assert solution_config[game_index]['seed'] == game.unit_generator.source_seed
        assert solution_config[game_index]['problemId'] == game_config['id']

        play(game, solution_config[game_index])
        game_index += 1

if __name__ == '__main__':
    main()
