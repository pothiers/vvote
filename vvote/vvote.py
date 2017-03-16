#! /usr/bin/env python3
"""Count ballots.
"""

import sys
import argparse
import logging
import sqlite3

from .sovc import Sovc
from .lvr import Lvr


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

            

#!schema = '''
#!CREATE TABLE race (
#!   race_id integer primary key,
#!   title text,
#!   num_to_vote_for integer,
#!);
#!CREATE TABLE choices (
#!  race_id integer,
#!  choice_id text,
#!);
#!CREATE TABLE cvr (
#!  cvr_id integer,
#!  race_id integer,
#!  choice_id text,
#!);
#!
#!'''    
#!def save_sovc_db(dbfile, votes, choices, n_votes, sovcfilename,
#!                 orderedraces=None,
#!                 na_tag='<OOD>'):
#!    """Save SOVC sqlite DB"""
#!    # votes[race][choice] = count
#!    # choices[race] = set([choice1, choice2,...])
#!    # n_votes[race] => num-to-vote-for
#!
#!    conn = sqlite3.connect(dbfile)
#!
#!    for race in orderedraces:
#!        nvotes = n_votes[race]
#!
#!        # sum values from N*undervote-N (N=[1..nvotes])
#!        undervotes = 0
#!        for n in range(1,nvotes+1):
#!            choice = 'undervote-{}'.format(n)
#!            undervotes += (n * votes[race][choice])
#!            ignore_choices.add(choice) 
#!        votes[race]['undervotes'] = undervotes
#!        choices[race].add('undervotes')
#!        
#!        for choice in set(choices[race]-ignore_choices):
#!            count = votes[race][choice]
#!            if choice == 'overvote':
#!                count*= nvotes
#!
#!            ws.cell(column=col, row=1, value="{}".format(race))
#!            ws.cell(column=col, row=3, value="{}".format(choice))
#!            ws.cell(column=col, row=4, value="{}".format(count))
#!            col += 1
#!    wb.save(sovcfilename)
#!    sovc.transpose(sovcfilename, '{}.transpose.xlsx'.format(sovcfilename))




def clean_choice(choice):
    "Systemic fix to strings given as choices in BALLOTS"
    if choice[:4] == 'DEM ':
        return choice[4:]
    if choice[:4] == 'REP ':
        return choice[4:]
    return choice.strip()
    



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
    parser.add_argument('LVRfile', type=argparse.FileType('r'),
                        help='Input LVR excel (.xslx) file')
    parser.add_argument('-t', '--talley', type=argparse.FileType('w'),
                        help='Vote count output (SOVC equiv)')
    parser.add_argument('-s', '--sovc', type=argparse.FileType('r'),
                        help=('Name of SOVC (xslx) file to compare to results.'
                              '(No comparison done if not given.)'))
    parser.add_argument('-f', '--format',
                        help='Format of output talley file.',
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
    args.LVRfile.close()
    args.LVRfile = args.LVRfile.name
    if args.talley:
        args.talley.close()
        args.talley = args.talley.name
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

    print('# Counting votes from file: {}'.format(args.LVRfile))
    lvr = Lvr(args.LVRfile)
    lvr.count_votes(verbose=args.verbose)
    # Vote counts now in: votes
    if args.format == 'text':
        lvr.emit_results(outputfile=args.talley)
    elif args.format == 'SOVC':
        lvr.write_sovc(args.talley)
        
    if args.sovc != None:
        sovc = Sovc(args.sovc)
        sovc.compare(lvr.votes, lvr.choices, lvr.n_votes)

if __name__ == '__main__':
    main()
