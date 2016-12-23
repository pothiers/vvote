#! /usr/bin/env python3
"""Count ballots.
"""

import sys
import argparse
import logging
from collections import defaultdict

from openpyxl import load_workbook

def OLD1_emit_results(votes, choices):
    #print('votes={}'.format(votes))
    # votes[race][choice] = count
    print("Ballot Counts:")
    for race in sorted(choices.keys()):
        print('  Race: "{}"'.format(race))
        for choice in sorted(choices[race]):
            print('    "{}" = {}'.format(choice,votes[race][choice]))

def emit_results(votes, choices, n_votes,
                 orderedraces=None,
                 na_tag=None, file=sys.stdout):
    # votes[race][choice] = count
    # choices[race] = set([choice1, choice2,...])
    # n_votes[race] => num-to-vote-for

    # Output the number of votes allowed for each race (to stdout)
    #! print('Vote for N:')
    #! for k,v in n_votes.items():
    #!     print('{}:\t{}'.format(v,k))

    for race in orderedraces:
        print(file=file)
        print(race, file=file)
        for choice in choices[race]:
            if choice == na_tag:
                n = n_votes[race]
                print('\t{}\t{}'.format(choice, int(votes[race][choice]/n)),
                      file=file)
            else:
                print('\t{}\t{}'.format(choice, votes[race][choice]),
                      file=file)

def count_votes(xslx_filename,
                outputfile=None,
                na_tag='<OOD>', # Out of District Ballots
                writeintag='Write-in',
                overvotetag='overvote',
                undervotetag='undervote'):
    wb = load_workbook(filename=xslx_filename, read_only=True)
    ws = wb.active
    nontitles = set(['Cast Vote Record',
                     'Serial Number',
                     'Precinct',
                     'Ballot Style'])
    choices = defaultdict(set) # choices[race] = set([choice1, choice2,...])
    votes = defaultdict(lambda : defaultdict(int)) # votes[race][choice] = cnt
    n_votes = defaultdict(int)  # n_votes[race] => num-to-vote-for

    coltitle = dict() # coltitle[column] => racetitle
    orderedraces = list()
    prevtitle = None
    ridx = 0
    for row in ws.rows:
        ridx += 1
        cidx = 0
        raceballot = list() # single ballot for single race
        for cell in row:
            cidx += 1

            # Ignore the (leading) columns that are not Race Titles
            if ridx == 1 and cell.value in nontitles:
                continue
            
            if ridx == 1: # header
                if cell.value != None:
                    race = cell.value
                    orderedraces.append(race)
                    n_votes[race] = 1
                    choices[race].add(undervotetag)
                    choices[race].add(overvotetag)
                    choices[race].add(na_tag)
                else: # vote-for-N race
                    n_votes[race] += 1
                coltitle[cidx] = race
            else: # ballots
                if cidx not in coltitle: # should never happen
                    continue
                
                if (cell.value == '' or cell.value == None):
                    choice = na_tag
                else:
                    choice = cell.value
                race = coltitle[cidx]
                next_race = coltitle[cidx+1] if cidx < ws.max_column else None
                raceballot.append(choice)
                if race != next_race: # finished one race, one ballot
                    #print('DBG-1: raceballot={}'.format(raceballot))
                    if undervotetag in raceballot:
                        undervote_m = ('undervote-{}'
                                       .format(raceballot.count(undervotetag)))
                        votes[race][undervote_m] += 1
                    if overvotetag in raceballot:
                        assert raceballot.count(overvotetag) == n_votes[race]
                        votes[race][undervotetag] += 1
                    if na_tag in raceballot:
                        assert raceballot.count(na_tag) == n_votes[race]
                        votes[race][na_tag] += 1
                    raceballot = [c for c in raceballot
                                  if ((c != undervotetag)
                                      and (c != overvotetag)
                                      and (c != na_tag)
                                      and (c != writeintag)
                                  )]
                    #! if len(raceballot) != len(set(raceballot)):
                    #!     print('raceballot[{}]={}'.format(ridx,raceballot))
                    assert len(raceballot) == len(set(raceballot)) # no dupes
                    for choice in set(raceballot):
                        choices[race].add(choice)
                        votes[race][choice] += 1
                    raceballot = list() # single ballot for single race

    # Vote counts now in: votes
    emit_results(votes, choices, n_votes, na_tag=na_tag,
                 orderedraces=orderedraces,
                 file=outputfile)
    print('Processed {} ballots'.format(ridx-1))
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
