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

import itertools
from openpyxl import load_workbook
from openpyxl import Workbook
from difflib import SequenceMatcher

from .sovc import Sovc
from .lvr import Lvr


def similar(a, b):
    "Symetric similarity.  Higher number is more similar."
    if a == b:
        return 99999
    #!return SequenceMatcher(a=a, b=b).ratio()+SequenceMatcher(a=b, b=a).ratio()
    return max(SequenceMatcher(a=a, b=b).ratio(),
               SequenceMatcher(a=b, b=a).ratio())

            

def gen_map(sovc_xslx, lvr_xslx, verbose=False):
    if verbose:
        print('Verbose enabled for: gen_map')
    sovc = Sovc(sovc_xslx)
    races_sovc, choices_sovc = sovc.get_titles()
    lvr = Lvr(lvr_xslx)
    races_lvr, choices_lvr = lvr.get_titles(verbose=verbose)
    racelut = dict() # lut[lvr] = sovc
    choicelut = dict() # lut[lvr] = sovc
    #!for rs,rc in itertools.product(races_sovc, races_lvr):

    for rs in races_sovc:
        maxscore = -1
        maxtitle = None
        for rc in races_lvr:
            score = similar(rs,rc)
            if score > maxscore:
                maxscore = score
                maxtitle = rs
                racelut[rc] = (maxtitle, score)

    for cs  in choices_sovc:
        maxscore = -1
        maxtitle = None
        for cc in choices_lvr:
            score = similar(cs,cc)
            if score > maxscore:
                maxscore = score
                maxtitle = cs
                choicelut[cc] = (maxtitle, score)
                
    return racelut, choicelut
            
##############################################################################

def main():
    "Parse command line arguments and do the work."
    #print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='Create string mapping (SOVC to LVR)',
        epilog='EXAMPLE: %(prog)s sovc.xslx lvr.xslx"'
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
        racelut, choicelut = gen_map(args.sovcfile, args.lvrfile,
                                     verbose=args.verbose)
    print('{}\t{}'.format('SOVC','LVR'), file=args.racemap)
    numout=0
    for lvr,(sovc,score) in racelut.items():
        #if sovc != lvr:
        if True:
            numout += 1
            print('{}\t{}\t{}'.format(sovc, lvr, score), file=args.racemap)
    print('Generated {}/{} records to map RACE strings from {} to {}'
          .format(numout, len(racelut), args.sovcfile, args.lvrfile))

    print('{}\t{}'.format('SOVC','LVR'), file=args.choicemap)
    numout=0
    for lvr,(sovc,score) in choicelut.items():
        #if sovc != lvr:
        if True:
            numout += 1
            print('{}\t{}\t{}'.format(sovc, lvr, score), file=args.choicemap)
    print('Generated {}/{} records to map CHOICE strings from {} to {}'
          .format(numout, len(choicelut), args.sovcfile, args.lvrfile))

if __name__ == '__main__':
    main()
