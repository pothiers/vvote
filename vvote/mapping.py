#! /usr/bin/env python3
"""Build mapping file between CVR and SOVC.
"""

# EXAMPLES:
#  genmap tests/data/mock1-sovc.xlsx tests/data/mock1.xlsx race1.csv choice1.csv
#  genmap tests/data/G2016_EXPORT1.xlsx tests/data/day-1-cvr.xlsx race.csv choice.csv



import sys
import argparse
import logging
from collections import defaultdict
from pprint import pprint

import itertools
from openpyxl import load_workbook
from openpyxl import Workbook
from difflib import SequenceMatcher

def similar(a, b):
    "RETURN similariry in range [0,1]"
    if a == b:
        return 999
    return SequenceMatcher(a=a, b=b).ratio() + SequenceMatcher(a=b, b=a).ratio()

def get_SOVC_titles(xslx_filename,
                    nrows = 10000, # progress every N rows iff verbose==True
                    verbose=False):
    "RETURN: dict[(race,choice)] => count"
    
    # Row 1:: Race titles (duplicated over columns representing choices)
    # Row 2:: party (we don't care)
    # Row 3:: Choices
    #
    # Col 7 to M:: vote counts
    wb = load_workbook(filename=xslx_filename)
    ws = wb.active
    totalsrow = ws.max_row - 1
    assert ws.cell(row=totalsrow, column=3).value == 'COUNTY TOTALS'
    races = set([ws.cell(row=1,column=c).value.strip()
                 for c in range(7,ws.max_column+1)])
    choices = set([ws.cell(row=3,column=c).value.strip()
                   for c in range(4,ws.max_column+1)])
    return races, choices

def get_CVR_titles(xslx_filename,
                   nrows = 10000, # progress every N rows iff verbose==True
                   verbose=False):
    "RETURN: dict[(race,choice)] => count"
    
    # Row 1:: Race titles (None over columns representing choices beyond first)
    # Row 2 to N:: Choices
    #
    # Col 4 to M::
    wb = load_workbook(filename=xslx_filename, read_only=True)
    ws = wb.active
    nontitles = set(['Cast Vote Record',
                     'Serial Number',
                     'Precinct',
                     'Ballot Style'])
    races = set()
    choices = set()
    ridx = 0
    for row in ws.rows:
        ridx += 1
        cidx = 0
        if verbose:
            if (ridx % nrows) == 0:
                print('# processed {} ballots'.format(ridx))
        for cell in row:
            cidx += 1
            if cidx < 4:
                continue
            # Ignore the (leading) columns that are not Race Titles
            if ridx == 1 and cell.value in nontitles:
                continue
            if ridx == 1: # header
                if cell.value != None:
                    races.add(cell.value.strip())

            else: #ballots
                if (cell.value == '' or cell.value == None or cell.value.strip() == ''):
                    continue
                choices.add(cell.value.strip())
    return races, choices

def gen_map(sovc_xslx, cvr_xslx, verbose=False):
    races_sovc, choices_sovc = get_SOVC_titles(sovc_xslx, verbose=verbose)
    races_cvr, choices_cvr = get_CVR_titles(cvr_xslx, verbose=verbose)
    racelut = dict() # lut[sovc] = cvr
    choicelut = dict() # lut[sovc] = cvr
    other = ['BALLOTS CAST', 'OVER VOTES', 'UNDER VOTES', 'VOTERS', 'WRITE-IN']
    #!for rs,rc in itertools.product(races_sovc, races_cvr):
    for rs in races_sovc:
        maxsim = 0
        maxcvr = None
        for rc in races_cvr:
            s = similar(rs,rc)
            if s > maxsim:
                maxsim = s
                maxcvr = rc
                racelut[rs] = maxcvr
    for cs  in choices_sovc:
        if cs in other:
            continue
        maxsim = 0
        maxcvr = None
        for cc in choices_cvr:
            s = similar(cs,cc)
            if s > maxsim:
                maxsim = s
                maxcvr = cc
                choicelut[cs] = maxcvr
                
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

    racelut, choicelut = gen_map(args.sovcfile, args.cvrfile,
                                 verbose=args.verbose)
    #print('RACE lut')
    #pprint(racelut)
    for sovc,cvr in racelut.items():
        if sovc != cvr:
            print('{}\t{}'.format(sovc,cvr), file=args.racemap)
    #print('CHOICE lut')
    #pprint(choicelut)
    for sovc,cvr in choicelut.items():
        if sovc != cvr:
            print('{}\t{}'.format(sovc,cvr), file=args.choicemap)

if __name__ == '__main__':
    main()
