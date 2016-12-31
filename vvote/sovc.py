#! /usr/bin/env python3
"""Extract from Statement Of Votes Cast
"""

import sys
import argparse
import logging
from collections import defaultdict
from pprint import pprint

from openpyxl import load_workbook
from openpyxl import Workbook

def transpose(in_xslx, out_xslx):
    wb = load_workbook(filename=in_xslx)
    ws = wb.active
    wb2 = Workbook()
    ws2 = wb2.active
    ws2.title = 'Transposed'

    for row in range(1,ws.max_row+1):
        for col in range(1,ws.max_column+1):
            ws2.cell(row=col, column=row,
                     value=ws.cell(row=row, column=col).value)
    wb2.save(filename=out_xslx)        

def get_totals(xslx_filename):
    "RETURN: dict[(race,choice)] => count"
    
    # Row 1:: Race titles (duplicated over columns representing choices)
    # Row 2:: party (we don't care)
    # Row 3:: Choices
    # Row 4 to N-1:: Precinct totals
    # Row N:: Grand totals (County totals)
    # Row N+1:: "_x001A_"  ??? End of data?
    #
    # Col 1:: County Number
    # Col 2:: Precinct Code (number)
    # Col 3:: Precinct Name (number) or "COUNTY TOTALS"
    # Col 4:: Registered Voters-Total
    # Col 5:: Ballots Cast-Total
    # Col 6:: Ballots Cast-Blank
    # Col 7 to M:: vote counts
    wb = load_workbook(filename=xslx_filename)
    ws = wb.active
    totalsrow = ws.max_row - 1
    assert ws.cell(row=totalsrow, column=3).value == 'COUNTY TOTALS'
    races = [ws.cell(row=1,column=c).value.strip()
             for c in range(4,ws.max_column+1)]
    choices = [ws.cell(row=3,column=c).value.strip()
               for c in range(4,ws.max_column+1)]
    totals = [ws.cell(row=totalsrow,column=c).value
              for c in range(4,ws.max_column+1)]
    racechoice = zip(races,choices)
    totdict = dict(zip(racechoice,totals))
    return totdict

##############################################################################

def main():
    "Parse command line arguments and do the work."
    #print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='Extract from Statement Of Votes Cast',
        epilog='EXAMPLE: %(prog)s sovc.xslx"'
        )
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('infile', type=argparse.FileType('r'),
                        help='Input file')
    #!parser.add_argument('outfile', type=argparse.FileType('w'),
    #!                    help='Vote count output')

    parser.add_argument('--csv',
                        action='store_true',
                        help='Write Excel to CSV file')

    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING')
    args = parser.parse_args()
    args.infile.close()
    args.infile = args.infile.name
    #args.outfile.close()
    #args.outfile = args.outfile.name

    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    print('Reading counts from file: "{}"'.format(args.infile))
    totdict = get_totals(args.infile)
    print('Totals = ',)
    pprint(totdict)

if __name__ == '__main__':
    main()
