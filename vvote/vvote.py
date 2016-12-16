#! /usr/bin/env python3
"""<<Python script callable from command line.  Put description here.>>
"""

import sys
import argparse
import logging
from collections import defaultdict

from openpyxl import load_workbook


def count_votes(xslx_filename, results):
    filename='/data/mock-election/CVR with SERIAL NUMBER.xlsx',
    wb = load_workbook(filename=xslx_filename, read_only=True)
    ws = wb.active
    #wb.sheetnames  # => ['Marked Sheet']
    #c = ws['A4']
    #c.value        # => 98060
    nontitles = set(['Cast Vote Record',
                     'Serial Number',
                     'Precinct',
                     'Ballot Style'])
    #titles = [c.value for c in list(ws.rows)[0]]
    #!print('titles={}'.format(titles))
    choices = defaultdict(set) # => choices[issue] = set([choice1, choice2,...])
    # votes[issue][choice] = count
    votes = defaultdict(lambda : defaultdict(int)) 
    coltitle = dict() # coltitle[column] => issuetitle
    prevtitle = None
    ridx = 0
    for row in ws.rows:
        ridx += 1
        cidx = 0
        for cell in row:
            cidx += 1
            #!print('row={}, col={}'.format(ridx, cidx))
            #!if cell.row == 2:
            #!    print('cidx={},coltitle={}'
            #!          .format(cidx, coltitle))

            value = '(empty)' if (cell.value == '' or cell.value == None) else cell.value
                
            if ridx == 1 and value in nontitles:
                continue
            
            if ridx == 1:
                title = prevtitle if value == None else value
                prevtitle = title
                coltitle[cidx] = title
            else:
                if cidx not in coltitle:
                    continue
                issue = coltitle[cidx]
                choice = value
                choices[issue].add(choice)
                votes[issue][choice] += 1

    # Debug
    #print('choices={}'.format(choices))
    #!print("Ballot Choices Used:")
    #!for issue,choices in choices.items():
    #!    print('  Issue: "{}"'.format(issue))
    #!    print('    Choices:')
    #!    for choice in choices:
    #!        print('  "{}"'.format(choice))
    #!print()

    # votes[issue][choice] = count
    #print('votes={}'.format(votes))
    print("Ballot Counts:")
    for issue in sorted(choices.keys()):
        print('  Issue: "{}"'.format(issue))
        for choice in sorted(choices[issue]):
            print('    "{} = {}'.format(choice,votes[issue][choice]))

    return votes,choices




##############################################################################

def main():
    "Parse command line arguments and do the work."
    print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('infile', type=argparse.FileType('r'),
                        help='Input file')
    parser.add_argument('outfile', type=argparse.FileType('w'),
                        help='Output output')

    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING')
    args = parser.parse_args()
    #!args.outfile.close()
    #!args.outfile = args.outfile.name

    #!print 'My args=',args
    #!print 'infile=',args.infile

    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    count_votes(args.infile, args.outfile)

if __name__ == '__main__':
    main()
