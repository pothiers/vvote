#! /usr/bin/env python3
"""Count ballots.
"""

import sys
import argparse
import logging
from collections import defaultdict

from openpyxl import load_workbook
from openpyxl import Workbook
from . import sovc


#!ballot2sovc = {
#!    #Ballot, SOVC
#!    'Write-in': 'WRITE-IN',
#!    'overvote': 'OVER VOTES',
#!    'undervote': 'UNDER VOTES',
#!    'YES/SÍ': 'YES/SI' ,
#!    'PRESIDENTIAL ELECTOR': 'PRESIDENTIAL ELECTORS',
#!    'U.S. SENATOR': 'UNITED STATES SENATOR',
#!    }
#!
#!def revlut(lut):
#!    "RETURN: new dict[a] => b from dict[b] => a"
#!    newlut = dict()
#!    for k,v in lut.items():
#!        newlut[v] = k
#!    return newlut
#!
#!sovc2ballot = revlut(ballot2sovc)
sovc2ballot = dict()

            

def compare_sovc(sovcfile, votes, choices, n_votes):
    print('Comparing calculated vote counts to those from {}'.format(sovcfile))
    totdict = sovc.get_totals(sovcfile)
    sovcraces = set([sovc2ballot.get(race,race)
                     for race,choice in totdict.keys()])
    balraces = set(votes.keys())

    for race in sovcraces - balraces:
            print('ERROR: Ballot votes do not contain race "{}".'.format(race))
    for race in balraces - sovcraces:
            print('ERROR: SOVC votes do not contain race "{}".'.format(race))
        
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
                print('ERROR: vote counts do not agree for {}. sovc={}, calc={}'
                      .format((race,choice), sovccount, votes[race][choice] ))

def emit_results(votes, choices, n_votes, num_ballots,
                 orderedraces=None,
                 na_tag='<OOD>', # Out of District Ballots
                 outputfile = None):
    # votes[race][choice] = count
    # choices[race] = set([choice1, choice2,...])
    # n_votes[race] => num-to-vote-for

    if outputfile == None:
        file=sys.stdout
    else:
        file = open(outputfile, mode='w')

    for race in orderedraces:
        print(file=file)
        print("{} (vote for {})".format(race, n_votes[race]), file=file)
        #for choice in sorted(choices[race]):
        special = set([k for k in votes[race].keys()
                       if k[:10] == 'undervote'])
        for choice in sorted(set(votes[race].keys()) - special):
            #!if choice == na_tag:
            #!    n = n_votes[race]
            #!    print('\t{}\t{}'.format(choice, int(votes[race][choice]/n)),
            #!          file=file)
            if choice != na_tag:
                print('\t{:10d}\t{}'.format(votes[race][choice], choice),
                      file=file)
        print('\t{:10d}\t{}'.format(num_ballots - votes[race][na_tag],
                                'IN-DISTRICT'),
              file=file)
        print('\t{:10d}\t{}'.format(votes[race][na_tag], 'OUT-OF-DISTRICT'),
              file=file)
    file.close()
    
def write_sovc(votes, choices, n_votes, sovcfilename,
               orderedraces=None,
               na_tag='<OOD>'):
    # votes[race][choice] = count
    # choices[race] = set([choice1, choice2,...])
    # n_votes[race] => num-to-vote-for

    # Row 1:: Race titles (merged over columns representing choices)
    # Row 2:: party (leave blank, we do not know)
    # Row 3:: Choices
    # Row 4:: Grand totals (County totals)

    wb = Workbook()
    ws = wb.active

    # Races
    ws['A1'] = 'COUNTY NUMBER'
    ws['B1'] = 'PRECINCT CODE'
    ws['C1'] = 'PRECINCT NAME'
    ws['D1'] = 'REGISTERED VOTERS - TOTAL'
    ws['E1'] = 'BALLOTS CAST - TOTAL'
    ws['F1'] = 'BALLOTS CAST - BLANK'
    # G1 ... :: Races (duplicated for each choice of same race)

    # Choices
    ws['D3'] = 'VOTERS'
    ws['E3'] = 'BALLOTS CAST'
    ws['F3'] = 'BALLOTS CAST'
    # G3 ... :: Candidates

    ws['B4'] = 'ZZZ'
    ws['C4'] = 'COUNTY TOTALS'
    ws['A5'] = '_x001A_'

    col = 7
    ignore_choices = set([na_tag])
    for race in orderedraces:
        nvotes = n_votes[race]

        # sum values from N*undervote-N (N=[1..nvotes])
        undervotes = 0
        for n in range(1,nvotes+1):
            choice = 'undervote-{}'.format(n)
            undervotes += (n * votes[race][choice])
            ignore_choices.add(choice) 
        votes[race]['undervotes'] = undervotes
        choices[race].add('undervotes')
        
        for choice in set(choices[race]-ignore_choices):
            count = votes[race][choice]
            if choice == 'overvote':
                count*= nvotes

            ws.cell(column=col, row=1, value="{}".format(race))
            ws.cell(column=col, row=3, value="{}".format(choice))
            ws.cell(column=col, row=4, value="{}".format(count))
            col += 1
    wb.save(sovcfilename)
    sovc.transpose(sovcfilename, '{}.transpose.xlsx'.format(sovcfilename))


def clean_choice(choice):
    "Systemic fix to strings given as choices in BALLOTS"
    if choice[:4] == 'DEM ':
        return choice[4:]
    if choice[:4] == 'REP ':
        return choice[4:]
    return choice.strip()
    
def count_votes(xslx_filename,
                verbose=False,
                nrows = 10000, # progress every N rows iff verbose==True
                na_tag='<OOD>', # Out of District Ballots
                writeintag='Write-in',
                overvotetag='overvote',
                undervotetag='undervote'):
    if verbose:
        print('# VERBOSE enabled')
    wb = load_workbook(filename=xslx_filename, read_only=True)
    ws = wb.active
    if (ws.max_row == 1) or (ws.max_column == 1):
        ws.max_row = ws.max_column = None
        # unzip -p /data/mock-election/Final_Count_LVR.xlsx | grep dimension
        ws.calculate_dimension(force=True)
    print('# maxCol={}, maxRow={}'.format(ws.max_column, ws.max_row))
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
        if verbose:
            if (ridx % nrows) == 0:
                print('# processed {} ballots'.format(ridx))
        for cell in row:
            cidx += 1
            #print('# DBG-0: ridx={} cidx{}'.format(ridx,cidx))

            # Ignore the (leading) columns that are not Race Titles
            if ridx == 1 and cell.value in nontitles:
                continue
            
            if ridx == 1: # header
                if cell.value != None:
                    race = cell.value.strip()
                    orderedraces.append(race)
                    n_votes[race] = 1
                    choices[race].add(overvotetag)
                    choices[race].add(writeintag)
                    choices[race].add(na_tag)
                else: # vote-for-N race
                    n_votes[race] += 1
                coltitle[cidx] = race
            else: # ballots
                if cidx not in coltitle:
                    # Skip columns we don't care about
                    continue
                
                if (cell.value == '' or cell.value == None):
                    choice = na_tag
                else:
                    #choice = clean_choice(cell.value)
                    choice = cell.value
                race = coltitle[cidx]
                next_race = coltitle[cidx+1] if cidx < ws.max_column else None
                #print('# DBG-0: race="{}"'.format(race))
                raceballot.append(choice)
                if race != next_race: # finished one race, one ballot
                    #print('DBG-1: raceballot={}'.format(raceballot))
                    if undervotetag in raceballot:
                        undervote_m = ('undervote-{}'
                                       .format(raceballot.count(undervotetag)))
                        votes[race][undervote_m] += 1
                        choices[race].add(undervote_m)
                    if overvotetag in raceballot:
                        assert raceballot.count(overvotetag) == n_votes[race]
                        votes[race][overvotetag] += 1
                    if na_tag in raceballot:
                        assert raceballot.count(na_tag) == n_votes[race]
                        votes[race][na_tag] += 1
                    for c in raceballot:
                        if c == writeintag:
                            choices[race].add(c)
                            votes[race][c] += 1                            
                    raceballot = [c for c in raceballot
                                  if ((c != undervotetag)
                                      and (c != overvotetag)
                                      and (c != na_tag)
                                      and (c != writeintag)
                                  )]
                    # no dupes
                    assert len(raceballot) == len(set(raceballot)), 'Duplicates in: {}'.format(raceballot)
    
                    for choice in set(raceballot):
                        choices[race].add(choice)
                        votes[race][choice] += 1
                    raceballot = list() # single ballot for single race

    nballots = ridx-1
    print('Processed {} ballots'.format(nballots))
    return votes, choices, n_votes, nballots, orderedraces




##############################################################################

def main():
    "Parse command line arguments and do the work."
    #print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='Count ballots.',
        epilog='EXAMPLE: %(prog)s --verbose --sovc /data/mock-election/G2016_EXPORT1.xlsx /data/mock-election/day-1-cvr.xlsx results1.txt'
        #  (49418 ballots)
        )
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('infile', type=argparse.FileType('r'),
                        help='Input file')
    parser.add_argument('outfile', type=argparse.FileType('w'),
                        help='Vote count output (SOVC equiv)')

    parser.add_argument('-s', '--sovc', type=argparse.FileType('r'),
                        help=('Name of SOVC (xslx) file to compare to results.'
                              '(No comparison done if not given.)'),
                        )
    parser.add_argument('-f', '--format',
                        help='Format of output file.',
                        choices=['text', 'SOVC'],
                        default='text')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Output progress')

    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING')
    args = parser.parse_args()
    args.infile.close()
    args.infile = args.infile.name
    args.outfile.close()
    args.outfile = args.outfile.name
    if args.sovc:
        args.sovc.close()
        args.sovc = args.sovc.name

    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])
    print('# Counting votes from file: {}'.format(args.infile))
    votes, choices, n_votes, nballots, races = count_votes(args.infile,
                                                           verbose=args.verbose)
    # Vote counts now in: votes
    if args.format == 'text':
        emit_results(votes, choices, n_votes, nballots,
                     orderedraces=races,
                     outputfile=args.outfile )
    elif args.format == 'SOVC':
        write_sovc(votes, choices, n_votes, args.outfile,
                   orderedraces=races)
        
    if args.sovc != None:
        compare_sovc(args.sovc, votes, choices, n_votes)

if __name__ == '__main__':
    main()
