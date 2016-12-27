#! /usr/bin/env python3
"""Extract from Statement Of Votes Cast
"""

import sys
import argparse
import logging
from collections import defaultdict

from openpyxl import load_workbook

def get_totals(xslx_filename):
    # Row 1:: Race titles (merged over columns representing choices)
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
    totals = [ws.cell(row=totalsrow,column=c).value
              for c in range(3,ws.max_column)]
    races = [ws.cell(row=1,column=c).value for c in range(3,ws.max_column)]
    totdict = dict(zip(races,totals)))

##############################################################################

def main():
    "Parse command line arguments and do the work."
    #print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('infile', type=argparse.FileType('r'),
                        help='Input file')
    parser.add_argument('outfile', type=argparse.FileType('w'),
                        help='Vote count output')

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
    get_totals(args.infile, outputfile=args.outfile)

if __name__ == '__main__':
    main()
