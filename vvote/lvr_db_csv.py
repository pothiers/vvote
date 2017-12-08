#! /usr/bin/env python
"""<<Python script callable from command line.  Put description here.>>
"""
# Docstrings intended for document generation via pydoc

import sys
import argparse
import logging
import csv
import os
import os.path

import sqlite3

# OUTPUT: CVR_id, Precinct, BallotStyle, (Race *), ...
def db_to_csv(dbfile, csv_filename, skip=1000):
        print('''NB: This produces a Sheet that may be very sparse.
The format is similar to LVR file from Elections software.
Writing to file: {} (after every {} records)'''.format(csv_filename, skip))
              
        race_sql = '''SELECT race_id as id, votesAllowed as numV, title
FROM race ORDER BY race_id;'''  

        votecvr_sql = '''
SELECT cvr.cvr_id as cid, cvr.precinct_code as pc, ballot_style as ball,
  choice.title as ct, vote.race_id as rid
FROM vote, choice, cvr
WHERE vote.cvr_id = cvr.cvr_id  AND vote.choice_id = choice.choice_id
ORDER BY vote.cvr_id ASC, vote.race_id ASC;'''


        conn = sqlite3.connect(dbfile)
        cur = conn.cursor()
        headers = 'Cast Vote Record,Precinct,Ballot Style'.split(',')
        raceVa = dict() # [id] => [votesAllowed, ...]
        raceName = dict() # [id] => [title, ...]
        all_races = list() # [rid, ...]
        for (rid,va,title) in cur.execute(race_sql):
            raceVa[rid] = va
            raceName[rid] = title
            all_races.append(rid) # insertion order
            headers.extend([title] * va)
            
        #logging.debug('raceName dict ({})={}'.format(len(raceName),raceName))

        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, dialect='excel')
            writer.writerow(headers)

            # A CSV row format is: [cvr, [race [choice, ...]]]
            # But query is essentially: [(cvr_id,race,choice), ...]
            # Query has gaps where no race (for CVR) or choice (for race).
            # Handle by aggregating lists with special handling at gaps.
            # Number of choice columns for a race = raceVa[id] (VotesAllowed)
            # ASSUME: rids from "all_races" and "votecvr_sql" are same order
            prev_cvr_id = None
            votes = list()    # [choice_title, ...]
            cvr_cols = list() 
            race_index = 0 # of "all_races"
            for (cvr_id,pc,ball,ct,rid) in cur.execute(votecvr_sql):
                if cvr_id != prev_cvr_id:     # new ROW (cvr)
                    if len(cvr_cols) > 0:
                        writer.writerow(cvr_cols + votes)

                    if (cvr_id % skip) == 0:
                        print('{}: row votes({})'.format(cvr_id,len(votes)))

                    # Reset
                    race_index = 0 # of "all_races"
                    votes = list()  # choices for this row
                    prev_cvr_id = cvr_id
                    # END new ROW

                cvr_cols=[cvr_id,pc,ball]
                # insert blank votes for races without data in this CVR
                while ((race_index < len(all_races))
                       and (rid != all_races[race_index])): 
                    votes.extend([''] * raceVa[all_races[race_index]])
                    race_index += 1

                votes.append(ct)
                # END votecvr_sql




##############################################################################

def main():
    "Parse command line arguments and do the work."
    #print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    dfdb='LVR.db'
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('dbfile', type=argparse.FileType('r'),
                        help='Input sqlite DB file')
    parser.add_argument('csvfile', type=argparse.FileType('w'),
                        help='Output CSV file')

    parser.add_argument('--skip', type=int, default=1000,
                        help='Amount of rows to skip before progress msg')
    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING')
    args = parser.parse_args()
    args.dbfile.close()
    args.dbfile = args.dbfile.name
    args.csvfile.close()
    args.csvfile = args.csvfile.name

    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    #logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    db_to_csv(args.dbfile, args.csvfile, skip=args.skip)
    print('Wrote {} to {}'.format(args.dbfile, args.csvfile))


if __name__ == '__main__':
    main()
