#! /usr/bin/env python3
"""Build mapping file between CVR and SOVC.
"""
# EXAMPLES:
# genmap tests/data/mock1-sovc.xlsx tests/data/mock1-cvr.xlsx r1.csv c1.csv
# genmap -v tests/data/day1-sovc.xlsx tests/data/day1-cvr.xlsx r.csv c.csv


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

from . import sovc
from . import cvr


def similar(a, b):
    "Symetric similarity.  Higher number is more similar."
    if a == b:
        return 99999
    #!return SequenceMatcher(a=a, b=b).ratio()+SequenceMatcher(a=b, b=a).ratio()
    return max(SequenceMatcher(a=a, b=b).ratio(),
               SequenceMatcher(a=b, b=a).ratio())

            
def get_SOVC_titles(excel_file,
                    nrows = 10000, # progress every N rows iff verbose==True
                    MARKER='_x001A_',
                    verbose=False):
    "RETURN: dict[(race,choice)] => count"
    
    # Row 1:: Race titles (duplicated over columns representing choices)
    # Row 2:: party (we don't care)
    # Row 3:: Choices
    #
    # Col 7 to M:: vote counts
    other = ['BALLOTS CAST', 'OVER VOTES', 'UNDER VOTES', 'VOTERS', 'WRITE-IN']
    ws = sovc.valid_SOVC(excel_file)
    totalsrow = ws.max_row - 1
    races = set([ws.cell(row=1,column=c).value.strip()
                 for c in range(7,ws.max_column+1)])
    choices = set([ws.cell(row=3,column=c).value.strip()
                   for c in range(4,ws.max_column+1)])
    return races, choices - set(other)

def get_CVR_titles(excel_file,
                   nrows = 10000, # progress every N rows iff verbose==True
                   verbose=False):
    "RETURN: dict[(race,choice)] => count"
    
    ws = cvr.valid_CVR(excel_file)
    other = ['undervote', 'Write-in']
    nontitles = set(['Cast Vote Record',
                     'Serial Number',
                     'Precinct',
                     'Ballot Style'])
    races = set()
    choices = set()
    ignorecolumns = set()
    ridx = 0
    for row in ws.rows:
        ridx += 1
        cidx = 0
        if verbose:
            if (ridx % nrows) == 0:
                print('# processed {} ballots'.format(ridx))
        for cell in row:
            cidx += 1
            if cidx in ignorecolumns:
                continue
            # Ignore the (leading) columns that are not Race Titles
            if ridx == 1 and cell.value in nontitles:
                ignorecolumns.add(cidx)
                continue
            if ridx == 1: # header
                if cell.value != None:
                    races.add(cell.value.strip())

            else: #ballots
                if (cell.value == '' or cell.value == None or cell.value.strip() == ''):
                    continue
                choices.add(cell.value.strip())
    return races, choices - set(other)

def gen_map(sovc_xslx, cvr_xslx, verbose=False):
    races_sovc, choices_sovc = get_SOVC_titles(sovc_xslx, verbose=verbose)
    races_cvr, choices_cvr = get_CVR_titles(cvr_xslx, verbose=verbose)
    racelut = dict() # lut[cvr] = sovc
    choicelut = dict() # lut[cvr] = sovc
    #!for rs,rc in itertools.product(races_sovc, races_cvr):
    for rc in races_cvr:
        maxsim = -1
        maxsovc = None
        for rs in races_sovc:
            s = similar(rs,rc)
            if s > maxsim:
                maxsim = s
                maxsovc = rs
                racelut[rc] = maxsovc

    for cc in choices_cvr:
        maxsim = -1
        maxsovc = None
        for cs  in choices_sovc:
            s = similar(cs,cc)
            if s > maxsim:
                maxsim = s
                maxsovc = cs
                choicelut[cc] = maxsovc
                
    return racelut, choicelut
            
##############################################################################

def main():
    "Parse command line arguments and do the work."
    #print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='Create string mapping (SOVC to CVR)',
        epilog='EXAMPLE: %(prog)s sovc.xslx cvr.xslx"'
        )
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('sovcfile', type=argparse.FileType('r'),
                        help='SOVC Excel (xslx) file')
    parser.add_argument('cvrfile', type=argparse.FileType('r'),
                        help='CVR Excel (xslx) file')
    parser.add_argument('racemap', type=argparse.FileType('w'),
                        help='Tab delimited LUT (SOVC -> CVR)')
    parser.add_argument('choicemap', type=argparse.FileType('w'),
                        help='Tab delimited LUT (SOVC -> CVR)')

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
    args.cvrfile.close()
    args.cvrfile = args.cvrfile.name

    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        racelut, choicelut = gen_map(args.sovcfile, args.cvrfile,
                                     verbose=args.verbose)
    print('{}\t{}'.format('SOVC','CVR'), file=args.racemap)
    numout=0
    for cvr,sovc in racelut.items():
        #if sovc != cvr:
        if True:
            numout += 1
            print('{}\t{}'.format(sovc,cvr), file=args.racemap)
    print('Generated {}/{} records to map RACE strings from {} to {}'
          .format(numout, len(racelut), args.sovcfile, args.cvrfile))

    print('{}\t{}'.format('SOVC','CVR'), file=args.choicemap)
    numout=0
    for cvr,sovc in choicelut.items():
        #if sovc != cvr:
        if True:
            numout += 1
            print('{}\t{}'.format(sovc,cvr), file=args.choicemap)
    print('Generated {}/{} records to map CHOICE strings from {} to {}'
          .format(numout, len(choicelut), args.sovcfile, args.cvrfile))

if __name__ == '__main__':
    main()
