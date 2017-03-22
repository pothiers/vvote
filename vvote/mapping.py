#! /usr/bin/env python3
"""Build mapping file between LVR and SOVC.
"""
# EXAMPLES:
# genmap tests/data/mock1-sovc.xlsx tests/data/mock1-lvr.xlsx r1.csv c1.csv
# genmap -v tests/data/day1-sovc.xlsx tests/data/day1-lvr.xlsx r.csv c.csv


import sys
import argparse
import logging
import warnings
from collections import defaultdict
from pprint import pprint
from os.path import basename

import itertools
from openpyxl import load_workbook
from openpyxl import Workbook
from difflib import SequenceMatcher

from .sovc import Sovc
from .lvr import Lvr


def similar(x,y):
    "Symetric similarity.  Higher number is more similar."
    if x == y:
        return 999
    a = x.replace(' ','')
    b = y.replace(' ','')
    #!return SequenceMatcher(a=a, b=b).ratio()+SequenceMatcher(a=b, b=a).ratio()
    return max(SequenceMatcher(a=a, b=b).ratio(),
               SequenceMatcher(a=b, b=a).ratio())

            

def gen_map(sovc_xslx, lvr_xslx,
            racematrix=None, # 'racematrix.csv',
            choicematrix=None, # 'choicematrix.csv'
            verbose=False):
    if verbose:
        print('Verbose enabled for: gen_map')

    sovc = Sovc(sovc_xslx)
    races_sovc = sovc.get_races()
    choices_sovc = sovc.get_choices()

    lvr = Lvr(lvr_xslx)
    races_lvr,choices_lvr = lvr.get_titles(verbose=verbose)

    if racematrix != None:
        with open(racematrix, mode='w') as rm:
            print('{}\t{}\t{}'.format('Race SOVC', 'LVR', 'Score', file=rm))
            for rsovc,rlvr in itertools.product(races_sovc, races_lvr):
                print('{}\t{}\t{}'.format(rsovc, rlvr, similar(rsovc,rlvr)),
                      file=rm)
        print('Wrote race mapping matrix to: {}'.format(racematrix))
    if choicematrix != None:
        with open(choicematrix, mode='w') as cm:
            print('{}\t{}\t{}'.format('Choice SOVC', 'LVR', 'Score', file=rm))
            for csovc,clvr in itertools.product(choices_sovc, choices_lvr):
                print('{}\t{}\t{}'.format(csovc, clvr, similar(csovc,clvr)),
                      file=cm)
        print('Wrote choice mapping matrix to: {}'.format(choicematrix))
            
    race_table = list() # [(sovc, lvr, score), ...]
    for rsovc in races_sovc:
        maxscore = -1
        best = None
        for rlvr in races_lvr:
            score = similar(rsovc,rlvr)
            if score > maxscore:
                maxscore = score
                #! best = rlvr
                best = rlvr if score > 0.5 else ''
        race_table.append((rsovc, best, maxscore))

    choice_table = list() # [(sovc, lvr, score), ...]
    for csovc  in choices_sovc:
        maxscore = -1
        best = None
        for clvr in choices_lvr:
            score = similar(csovc,clvr)
            if score > maxscore:
                maxscore = score
                #! best = clvr
                best = clvr if score > 0.5 else ''
        choice_table.append((csovc, best, maxscore))
                
    return sorted(race_table), sorted(choice_table)
            
##############################################################################

def main():
    "Parse command line arguments and do the work."
    #print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='Create string mapping (SOVC to LVR)',
        epilog='EXAMPLE: %(prog)s sovc.xslx lvr.xslx'
        )
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('sovcfile', type=argparse.FileType('r'),
                        help='SOVC Excel (xslx) file')
    parser.add_argument('lvrfile', type=argparse.FileType('r'),
                        help='LVR Excel (xslx) file')
    parser.add_argument('racemap', type=argparse.FileType('w'),
                        help='Tab delimited LUT (SOVC -> LVR)')
    parser.add_argument('choicemap', type=argparse.FileType('w'),
                        help='Tab delimited LUT (SOVC -> LVR)')

    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Output progress')
    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING')
    args = parser.parse_args()
    args.sovcfile.close()
    args.sovcfile = args.sovcfile.name
    args.lvrfile.close()
    args.lvrfile = args.lvrfile.name

    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    #######################
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        race_table, choice_table = gen_map(args.sovcfile, args.lvrfile,
                                     verbose=args.verbose)
    #!print('{}\t{}\t{}'.format('SOVC','LVR', 'Score'), file=args.racemap) 
    print('{}\t{}'.format('SOVC','LVR'), file=args.racemap) 
    numout=0
    for (sovc,lvr,score) in race_table:
        #if sovc != lvr:
        if True:
            numout += 1
            #!print('{}\t{}\t{}'.format(sovc, lvr, score), file=args.racemap)
            print('{}\t{}'.format(sovc, lvr), file=args.racemap)
    print('Generated {}/{} records to map RACE strings from {} to {}'
          .format(numout, len(race_table),
                  basename(args.sovcfile), basename(args.lvrfile)))

    #!print('{}\t{}\t{}'.format('SOVC','LVR', 'Score'), file=args.choicemap)
    print('{}\t{}'.format('SOVC','LVR'), file=args.choicemap)
    numout=0
    for (sovc, lvr, score) in choice_table:
        #if sovc != lvr:
        if True:
            numout += 1
            #!print('{}\t{}\t{}'.format(sovc, lvr, score), file=args.choicemap)
            print('{}\t{}'.format(sovc, lvr), file=args.choicemap)
    print('Generated {}/{} records to map CHOICE strings from {} to {}'
          .format(numout, len(choice_table), args.sovcfile, args.lvrfile))

if __name__ == '__main__':
    main()
