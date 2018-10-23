#! /usr/bin/env python
"""Manage LVR database.

- Load from Official ballots file(s). Named *LVR*.xlsx or *CVR*.xlsx
  into SQLITE database.

LVR :: List of CVR records (an excel file, each row is CVR except
     header row=1) Each record is the ballot results from one person.

Underlying dimensionality of LVR Data (value is Choice(string)):
1. CVR
2. Race

EXAMPLES:
  lvrdb    $edata/P-2018-CRV-2.csv
  lvrdb -s $edata/P-2018-CRV-*.csv 
"""
import sys
import argparse
import logging
import os
import os.path
import sqlite3
from collections import defaultdict
from pprint import pprint, pformat

import lvr.sql
from lvr.lvr_sheet import LvrSheet


class LvrDb():
    """Manage LVR Database (sqlite3 format)"""
    fixed_choices = ['overvote', 'undervote', 'Write-in']
    
    def __init__(self, dbfile):
        self.dbfile = dbfile
        self.sourcefile = None
        self.conn = None
        #!self.raceLut = dict() # lut[column] => raceId
        self.raceLut = None # lut[column] => raceId
        self.sheetRaceLut = None

    def new_db(self, overwrite=True):
        dbfile = self.dbfile
        if overwrite:
            if os.path.exists(dbfile):
                os.remove(dbfile)
                #print('Removed LVR database: {}'.format(dbfile))

        self.conn = sqlite3.connect(dbfile)
        cur = self.conn.cursor()
        cur.executescript(lvr.sql.lvr_schema)
        #print('Created schema in LVR database: {}'.format(dbfile))
        self.conn.commit()

    def close_db(self):
        if self.conn:
            self.conn.commit()
            self.conn.close()

    def summary(self):
        print('Summarize database: {}'.format(self.dbfile))
        self.conn = sqlite3.connect(self.dbfile)
        cur = self.conn.cursor()
        cur.execute('SELECT filename FROM source;')
        self.sourcefile = cur.fetchone()[0]
        cur.execute(
            'SELECT num_to_vote_for,count(choice.race_id) FROM choice,race'
            ' WHERE choice.race_id = race.race_id'
            ' GROUP BY race.race_id ORDER BY race.race_id;')
        va_choice_list = [(int(r[0]),int(r[1])) for r in cur.fetchall()]
        print('''
LVR Database Summary:
   FILENAME: {} # CSV source
   Race count: {}
   Count (VoteFor,Choices) per race: \n{}
###################################################################
'''.format(self.sourcefile,
           len(va_choice_list),
           ','.join([str(v) for v in va_choice_list]),  ))

    def insert_LVR_from_csv(self,csvfile):
        """Append to existing Sqlite DB."""
        sheet = LvrSheet(csvfile)
        self.sourcfile = sheet.filename
        cur = self.conn.cursor()
        cells = sheet.cells
        if self.sheetRaceLut==None:
            self.sheetRaceLut = sheet.raceLut
        #print('Inserting LVR CSV content into db: {}'.format(self.dbfile))

        choices = defaultdict(set) # of choice_title for each race
        choiceInvLut = dict() # lut[(raceId,choiceTitle)] => choiceId
        
        cur.execute('INSERT INTO source VALUES (?)', (csvfile,))

        # INSERT races
        if self.raceLut == None:
            self.raceLut = dict()
            for racename,raceC in sorted(self.sheetRaceLut.items(),
                                         key=lambda x: x[0]):
                # raceC (sheetColumnNumber) is surrogate for sort order
                cur.execute('INSERT INTO race VALUES (?,?,?,?)',
                            (None,  racename, raceC, sheet.voteFor[racename]))
                raceId = cur.lastrowid
                self.raceLut[raceC] = raceId
        # INSERT choices, cvr, vote
        for r in range(sheet.minDataR, sheet.max_row + 1):
            cvr_id = cells[r][1]
            precinct = cells[r][2]
            ballot = cells[r][3]

            cur.execute('INSERT INTO cvr VALUES (?,?,?)',
                        (cvr_id, precinct, ballot))
            #logging.debug('INSERT cvr: {}'.format(cvr_id))

            for c in range(sheet.minDataC, sheet.max_col + 1):

                try:
                    if self.sheetRaceLut[cells[1][c]] in self.raceLut:
                        race_id = self.raceLut[self.sheetRaceLut[cells[1][c]]]
                except Exception as err:
                    logging.error('Problem getting RACE_ID; {}'.format(err))
                    logging.debug('DBG: raceLutc={}'
                                  .format(pformat(self.raceLut)))
                    logging.debug('DBG: c={}'.format(c))
                    logging.debug('DBG: cells[1][c]={}'.format(cells[1][c]))
                    logging.debug('DBG: sheetRaceLut[cells[1][c]]={}'
                                  .format(self.sheetRaceLut[cells[1][c]]))
                    sys.exit()
                    
                choice_title = cells[r].get(c,None)
                if choice_title == None: continue

                if (race_id,choice_title) not in choiceInvLut:
                    party = 'NA'
                    cur.execute('INSERT INTO choice VALUES (?,?,?,?)',
                                (None, choice_title, race_id, party))
                    choice_id = cur.lastrowid
                    choiceInvLut[(race_id,choice_title)] = choice_id
                    
                cur.execute('INSERT INTO vote VALUES (?,?)',
                            (cvr_id, choiceInvLut[(race_id,choice_title)]))

    def insert_LVR_files(self,csvfiles):
        if len(csvfiles) > 0:
            self.new_db(overwrite=True)
        for csvfile in csvfiles:
            print('Adding CSV ({}) content to LVR database {}'
                  .format(csvfile, self.dbfile))
            self.insert_LVR_from_csv(csvfile)
        if len(csvfiles) > 0:
            self.close_db()    
        

##############################################################################

def main():
    "Parse command line arguments and do the work."
    parser = argparse.ArgumentParser(
        description='Load election results into DB',
        epilog='EXAMPLE: %(prog)s lvr1.csv ..."'
        )
    dfdb='LVR.db'
    parser.add_argument('LVRfiles', nargs='*',
                        help='Load these LVR files (CSV format) into DB.')

    parser.add_argument('--version', action='version', version='1.1.0')
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
    #!logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    db = LvrDb(args.database)
    db.insert_LVR_files(args.LVRfiles)
        
    #!db.to_csv(foo)
    #!print('Created CSV from DB in {}'.format(foo))
    if args.summary:
        db.summary()
    
if __name__ == '__main__':
    main()
