#! /usr/bin/env python3
"""Extract from Statement Of Votes Cast (SOVC)
"""

import sys
import argparse
import logging
from collections import defaultdict
from pprint import pprint

from openpyxl import load_workbook


class Sovc():
    """Maintain Statement Of Votes Cast (SOVC). Its an excel (.xslx) file
that represents official results.

   Row 1:: Race titles (duplicated over columns representing choices)
   Row 2:: party (we don't care)
   Row 3:: Choices
   Row 4 to N-1:: Precinct totals
   Row N:: Grand totals (County totals)
   Row N+1:: "_x001A_"  ??? End of data?
  
   Col 1:: County Number ('_x001A_' in last row)
   Col 2:: Precinct Code (number)
   Col 3:: Precinct Name (number) or "COUNTY TOTALS"
   Col 4:: "REGISTERED VOTERS - TOTAL" (Row 1)
   Col 5:: Ballots Cast-Total
   Col 6:: Ballots Cast-Blank
   Col 7 to M:: vote counts
"""
    MARKER='_x001A_'
    MARKER2='REGISTERED VOTERS - TOTAL'
    
    def __init__(self, sovc_file,
                 nrows = 10000, # progress every N rows iff verbose==True
                 verbose=False):
        wb = load_workbook(filename=sovc_file, read_only=True)
        ws = wb.active
        if (ws.max_row == 1) or (ws.max_column == 1):
            ws.max_row = ws.max_column = None
            ws.calculate_dimension(force=True)
        totalsrow = ws.max_row - 1        
        if verbose:
            print('DBG: file={}, ws.max_row = {}, ws.max_column = {}'
                  .format(sovc_file, ws.max_row, ws.max_column))

        # Validate format/content
        if ws.cell(row=1, column=4).value.strip() != self.MARKER2:
            msg = ('Row={}, Col={} is "{}" but expected "{}"'
                   .format(1, 4,
                           ws.cell(row=1, column=4).value,
                           self.MARKER2 ))
            raise 'Invalid SOVC ({}); {}'.format(sovc_file, msg)

        if ws.cell(row=totalsrow+1, column=1).value.strip() != self.MARKER:
            msg = ('Row={}, Col={} is "{}" but expected "{}"'
                   .format(totalsrow, 1,
                           ws.cell(row=totalsrow+1, column=1).value,
                           self.MARKER ))
            raise 'Invalid SOVC ({}); {}'.format(sovc_file, msg)
        if ws.cell(row=totalsrow, column=3).value != 'COUNTY TOTALS':
            msg = ('Row={}, Col={} is "{}" but expected "COUNTY TOTALS"'
                   .format(totalsrow, 3,
                           ws.cell(row=totalsrow, column=3).value))
            raise 'Invalid SOVC ({}); {}'.format(sovc_file, msg)

        self.filename = sovc_file
        self.totalsrow = totalsrow
        self.ws = ws
        self.max_row = ws.max_row
        self.max_column = ws.max_column


    def get_totals(self):
        "RETURN: dict[(race,choice)] => count"
        races = [self.ws.cell(row=1, column=c).value.strip()
                 for c in range(4, self.max_column+1)]
        choices = [self.ws.cell(row=3, column=c).value.strip()
                   for c in range(4, self.max_column+1)]
        totals = [self.ws.cell(row=self.totalsrow, column=c).value
                  for c in range(4, self.max_column+1)]
        racechoice = zip(races, choices)
        totdict = dict(zip(racechoice, totals))
        return totdict

    def compare(self, votes, choices, n_votes):
        print('Comparing calculated vote counts to those from {}'
              .format(self.filename))
        sovc2ballot = dict()
        ballot2sovc = dict()

        totdict = self.get_totals()
        sovcraces = set([sovc2ballot.get(race,race)
                         for race,choice in totdict.keys()])
        balraces = set(votes.keys())

        for race in sovcraces - balraces:
                print('ERROR: Ballot votes do not contain race "{}".'
                      .format(race))
        for race in balraces - sovcraces:
                print('ERROR: SOVC votes do not contain race "{}".'
                      .format(race))

        for race in sovcraces & balraces:
            sovcchoices = set([sovc2ballot.get(choice,choice)
                               for r,choice in totdict.keys() if r == race])
            balchoices = set(choices[race])
            for choice in sovcchoices - balchoices:
                print('ERROR: Ballot choices for race "{}" do not contain "{}".'
                      .format(race, choice))
            for choice in balchoices - sovcchoices :
                print('ERROR: SOVC choices for race "{}" do not contain "{}".'
                      .format(race, choice))
            for choice in sovcchoices & balchoices :
                sovccount = totdict[(ballot2sovc.get(race,race),
                                     ballot2sovc.get(choice,choice))]
                if votes[race][choice] != sovccount:
                    print(('ERROR: vote counts do not agree for {}. '
                          'sovc={}, calc={}')
                          .format((race, choice),
                                  sovccount,
                                  votes[race][choice]))

    def get_races(self):
        return set([self.ws.cell(row=1, column=c).value.strip()
                   for c in range(7, self.max_column+1)])

    def get_choices(self):
        other = ['BALLOTS CAST', 'OVER VOTES', 'UNDER VOTES',
                 'VOTERS', 'WRITE-IN']
        choices = set([self.ws.cell(row=3, column=c).value.strip()
                       for c in range(4, self.max_column+1)])
        #!return choices - set(other)
        return choices

##############################################################################

def main():
    "Parse command line arguments and do the work."
    #print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='Extract from Statement Of Votes Cast',
        epilog='EXAMPLE: %(prog)s sovc.xslx'
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
    sovc = Sovc(args.infile)
    totdict = sovc.get_totals()
    print('Totals = ',)
    pprint(totdict)

if __name__ == '__main__':
    main()
