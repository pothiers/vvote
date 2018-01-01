#! /usr/bin/env python
"""Manage SOVC database.

- Load from Official Election Results excel file(s).

SOVC :: Statement Of Votes Cast; official election results

Underlying dimensionality of SOVC Data (value is count-of-votes):
1. Precinct (many-to-one County)
2. Race
3c. Choice
"""

import sys
import argparse
import logging
import csv
import os
import os.path
import sqlite3
from collections import defaultdict
from pprint import pprint, pformat

from . import sql
from .sovc_sheet import SovcSheet

##############################################################################
### Database
###

class SovcDb():
    """Manage SOVC Database (sqlite3 format)"""
    #fixed_choices = set(['OVER VOTES', 'UNDER VOTES', 'WRITE-IN'])

    def __init__(self, dbfile):
        self.dbfile = dbfile
        self.source = None
        self.conn = None
        self.sourcefile = None
        #self.new_db(dbfile, sourcesheet.filename)
        

    def new_db(self,  overwrite=True):
        dbfile = self.dbfile
        if overwrite:
            if os.path.exists(dbfile):
                os.remove(dbfile)
                #! print('Removed SOVC database: {}'.format(dbfile))

        self.conn = sqlite3.connect(dbfile)
        cur = self.conn.cursor()
        cur.executescript(sql.sovc_schema)
        #print('Created schema in SOVC database: {}'.format(dbfile))
        self.conn.commit()

    def close(self):
        self.conn.commit()
        self.conn.close()

    def summary(self):
        print('Summarize database: {}'.format(self.dbfile))
        self.conn = sqlite3.connect(self.dbfile)
        cur = self.conn.cursor()
        cur.execute('SELECT filename FROM source;')
        self.sourcefile = cur.fetchone()[0]
        cur.execute('SELECT num_to_vote_for,count(choice.race_id)'
                    ' FROM choice,race'
                    ' WHERE choice.race_id = race.race_id'
                    ' GROUP BY race.race_id ORDER BY race.race_id;')

        va_choice_list = [(int(r[0]),int(r[1])) for r in cur.fetchall()]
        print('''
SOVC Database Summary:
   FILENAME: {} # CSV source
   Race count: {}
   Count (VoteFor,Choices) per race: \n{}
###################################################################
'''.format(self.sourcefile,
           len(va_choice_list),
           ','.join([str(v) for v in va_choice_list]),  ))

    def insert_from_csv(self, csvfile):
        """Append to existing Sqlite DB (or create new one). """
        self.new_db(overwrite=True)
        sovcsheet = SovcSheet(csvfile)
        self.sourcefile = sovcsheet.filename
        choices = defaultdict(set) # of choice_title for each race
        cur = self.conn.cursor()
        cells = sovcsheet.cells

        cur.execute('INSERT INTO source VALUES (?)', (csvfile,))
        
        (race_list, choice_list) = sovcsheet.get_race_lists()
        #!print('DBG: race_list={}'.format(pformat(race_list)))
        self.insert_race_list(race_list)
        self.insert_choice_list(choice_list)
        # common choices are cooked into SOVC headers
        #@@@ self.insert_common_choice_list(race_list)

        (precinct_list, vote_list) = sovcsheet.get_precinct_votes()
        self.insert_precinct_list(precinct_list)        
        self.insert_vote_list(vote_list)        

        self.close()
        #!logging.debug('DBG: Created RACE and CHOICE tables in {}'
        #!              .format(self.dbfile))
        #!sovcsheet.summary()
        
    def insert_race_list(self, race_list):
        """race_list:: [(race_id, title, num_to_vote_for), ...]"""
        cur = self.conn.cursor()
        cur.executemany('INSERT INTO race VALUES (?,?,?)', race_list)

    def insert_choice_list(self, choice_list):
        """choice_list:: [(choice_id, title, race_id, party), ...]"""
        cur = self.conn.cursor()
        cur.executemany('INSERT INTO choice VALUES (?,?,?,?)',choice_list)
        
    def insert_precinct_list(self, precinct_list):
        """
        precinct_list::
        [(-- race_id, # choice_id links to race_id
          choice_id,
          county_number,
          precinct_code,
          precinct_name,
          num_registered_voters,
          ballots_cast_total,
          ballots_cast_blank,
          ), ...]"""
        cur = self.conn.cursor()
        cur.executemany('INSERT INTO precinct VALUES (?,?,?,?,?,?,?)',
                        precinct_list)
    
    def insert_vote_list(self, vote_list):
        """vote_list:: [(choice_id, precinct_code, count), ...]"""
        cur = self.conn.cursor()
        cur.executemany('INSERT INTO vote VALUES (?,?,?)', vote_list)
        
    # OUTPUT: Race, NumToVoteFor, Choice, ChoiceId, ...
    def to_csv(self,csv_filename):
        self.conn = sqlite3.connect(self.dbfile)
        cur = self.conn.cursor()

        rc_list = [(row['rt'], row['ct'], row['cid'])
                   for row in cur.execute(sql.sovc_choice)]
        headers1 = ('COUNTY NUMBER,PRECINCT CODE,PRECINCT NAME,'
                    'REGISTERED VOTERS - TOTAL,BALLOTS CAST - TOTAL,'
                    'BALLOTS CAST - BLANK').split(',')
        headers1.extend([r for r,nv,c,cid in rc_list])        
        headers2 = ['Number to Vote For ->', '','','','','']
        headers2.extend([nv for r,nv,c,cid in rc_list])
        headers3 = ['Choice ->', '','','','','']
        headers3.extend([c for r,nv,c,cid in rc_list])
        
        #!fns = 'county,pcode,pname,totvot,totbal,blankbal'.split(',')
        #!fns.extend([c for r,c in rc_list])
        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, dialect='excel')
            writer.writerow(headers1)
            writer.writerow(headers2)
            writer.writerow(headers3)
            # loop over:
            #   Precinct (by County/Precinct),
            #   Race+Choice (by Race/Choice
            for row in cur.execute(sql.sovc_precinct):
                c6 = [row['county'], row['pcode'], row['pname'],
                      row['totvot'], row['totbal'],row['blankbal']]
                votes_list = list()
                for row in cur.execute(sql.sovc_race): # for one precinct
                    votes_list.append(row['count'])
                writer.writerow(c6 + votes_list)
            

### end SovcDb
##############################################################################





##############################################################################

def main():
    "Parse command line arguments and do the work."
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    dfdb='SOVC.db'
    parser.add_argument('--version', action='version', version='1.0.1')

    parser.add_argument('--incsv', type=argparse.FileType('r'),
                        help='Input CSV file to store into DB')
    parser.add_argument('-d', '--database', 
                        default=dfdb,
                        help=('SQlite database file to hold content.'
                              '  [default="{}"]').format(dfdb))
    parser.add_argument('--summary', '-s', action='store_true',
                        help='Summarize database content.')

    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING')
    args = parser.parse_args()


    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    db = SovcDb(args.database)
    if args.incsv:
        args.incsv.close()
        args.incsv = args.incsv.name
        db.insert_from_csv(args.incsv)

    if args.summary:
        db.summary()
    
if __name__ == '__main__':
    main()
