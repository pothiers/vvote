#! /usr/bin/env python3
"""<<Python script callable from command line.  Put description here.>>
"""

import sys
import argparse
import logging
from collections import defaultdict

from openpyxl import load_workbook

def OLD1_emit_results(votes, choices):
    #print('votes={}'.format(votes))
    # votes[issue][choice] = count
    print("Ballot Counts:")
    for issue in sorted(choices.keys()):
        print('  Issue: "{}"'.format(issue))
        for choice in sorted(choices[issue]):
            print('    "{}" = {}'.format(choice,votes[issue][choice]))

def emit_results(votes, choices, n_votes,
                 orderedissues=None,
                 na_choice=None, file=sys.stdout):
    # votes[issue][choice] = count
    # choices[issue] = set([choice1, choice2,...])
    # n_votes[issue] => num-to-vote-for

    # Output the number of votes allowed for each issue (to stdout)
    print('Vote for N:')
    for k,v in n_votes.items():
        print('{}:\t{}'.format(v,k))

    for issue in orderedissues:
        print(file=file)
        print(issue, file=file)
        for choice in choices[issue]:
            if choice == na_choice:
                n = n_votes[issue]
                print('\t{}\t{}'.format(choice, int(votes[issue][choice]/n)),
                      file=file)
            else:
                print('\t{}\t{}'.format(choice, votes[issue][choice]),
                      file=file)

def count_votes(xslx_filename,
                outputfile=None,
                na_choice=' Out of District Ballots'):
    wb = load_workbook(filename=xslx_filename, read_only=True)
    ws = wb.active
    nontitles = set(['Cast Vote Record',
                     'Serial Number',
                     'Precinct',
                     'Ballot Style'])
    choices = defaultdict(set) # choices[issue] = set([choice1, choice2,...])
    votes = defaultdict(lambda : defaultdict(int)) # votes[issue][choice] = cnt
    coltitle = dict() # coltitle[column] => issuetitle
    orderedissues = list()
    prevtitle = None
    ridx = 0
    need_nvotes = True
    for row in ws.rows:
        ridx += 1
        cidx = 0
        for cell in row:
            cidx += 1

            # Ignore the (leading) columns that are not Issue Titles
            if ridx == 1 and cell.value in nontitles:
                continue
            
            if ridx == 1:
                if cell.value == None:
                    title = prevtitle
                else:
                    title = cell.value
                    orderedissues.append(title)

                prevtitle = title
                coltitle[cidx] = title
            else:
                if need_nvotes:
                    # n_votes[issue] => num-to-vote-for
                    n_votes = defaultdict(int) 
                    for k,v in coltitle.items():
                        n_votes[v] += 1
                    need_nvotes = False
                
                if (cell.value == '' or cell.value == None):
                    value = na_choice
                else:
                    value = cell.value

                if cidx in coltitle:
                    issue = coltitle[cidx]
                    choice = value
                    choices[issue].add(choice)
                    votes[issue][choice] += 1

    # Vote counts now in: votes
    emit_results(votes, choices, n_votes, na_choice=na_choice,
                 orderedissues=orderedissues,
                 file=outputfile)
    return votes,choices




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
    print('Counting votes from file: "{}"'.format(args.infile))
    count_votes(args.infile, outputfile=args.outfile)

if __name__ == '__main__':
    main()
