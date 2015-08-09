import emu
import locker

import argparse
import json
import logging

class Evaluator:
    @staticmethod
    def play(game, score_func):
        pass

    @staticmethod
    def evaluate(config, score_func):
        if len(config['sourceSeeds']) == 0: return 0.0

        max_score, min_score = 0, 0
        total_score = 0

        for game in emu.GameGenerator(config):
            Evaluator.play(game, score_func)

            cur_score = game.line_score() + game.phrase_score()
            total_score += cur_score

            min_score = min(min_score, cur_score)
            max_score = max(max_score, cur_score)

        average_score = total_score // len(config['sourceSeeds'])

        print 'Board #%d:' % config['id']
        print '  min / max score: %d / %d' % (min_score, max_score)
        print '  average score: %d' % int(average_score)

        return average_score

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', '-f')
    parser.add_argument('--output_file', '-o')

    args = parser.parse_args()
    config = json.load(open(args.file))

    Evaluator.evaluate(config, None)

if __name__ == '__main__':
    main()
