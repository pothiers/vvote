#! /usr/bin/env python
"""Manage LVR database.

- Load from Official ballots file(s). Named *LVR*.xlsx or *CVR*.xlsx
  into SQLITE database.

LVR :: List of CVR records (an excel file, each row is CVR except
     header row=1) Each record is the ballot results from one person.

Underlying dimensionality of LVR Data (value is Choice(string)):
1. CVR
2. Race
"""

import sys
import argparse
import logging
import os
import os.path
import sqlite3
from collections import defaultdict
from pprint import pprint, pformat

#!from . import sql
#!from .lvr_sheet import LvrSheet
import vvote.sql
from vvote.lvr_sheet import LvrSheet


class LvrDb():
    """Manage LVR Database (sqlite3 format)"""
    fixed_choices = ['overvote', 'undervote', 'Write-in']
    
    def __init__(self, dbfile):
        self.dbfile = dbfile
        self.sourcefile = None
        self.conn = None
        self.raceLut = dict() # lut[column] => raceId

    def new_db(self, overwrite=True):
        dbfile = self.dbfile
        if overwrite:
            if os.path.exists(dbfile):
                os.remove(dbfile)
                #print('Removed LVR database: {}'.format(dbfile))

        self.conn = sqlite3.connect(dbfile)
        cur = self.conn.cursor()
        cur.executescript(vvote.sql.lvr_schema)
        #print('Created schema in LVR database: {}'.format(dbfile))
        self.conn.commit()

    def close_db(self):
        self.conn.commit()
        self.conn.close()

    def summary(self):
        print('Summarize database: {}'.format(self.dbfile))
        self.conn = sqlite3.connect(self.dbfile)
        cur = self.conn.cursor()
        cur.execute('SELECT filename FROM source;')
        self.sourcefile = cur.fetchone()[0]
        cur.execute('SELECT votesAllowed,count(choice.race_id) FROM choice,race'
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

    # Do not due this.  Data may contain these choices. If so, there
    # end up being two choice_ids for same choice_title
    def OBSOLETE_insert_fixed_choices(self, race_id, choiceInvLut):
        """Choices for ALL races, all elections: over/undervote, write-in.
choiceInvLut :: lut[choiceTitle] => choiceId; MODIFIED IN PLACE
"""
        cur = self.conn.cursor()
        for choice_title in self.fixed_choices:
            cur.execute('INSERT INTO choice VALUES (?,?,?)',
                        (None, choice_title, race_id))
            choice_id = cur.lastrowid
            choiceInvLut[choice_title] = choice_id
        
    def insert_from_csv(self,csvfile):
        """Append to existing Sqlite DB."""
        self.new_db(overwrite=True)
        sheet = LvrSheet(csvfile)
        self.sourcfile = sheet.filename
        cur = self.conn.cursor()
        cells = sheet.cells

        #print('Inserting LVR CSV content into db: {}'.format(self.dbfile))

        choices = defaultdict(set) # of choice_title for each race
        choiceInvLut = dict() # lut[(raceId,choiceTitle)] => choiceId
        
        cur.execute('INSERT INTO source VALUES (?)', (csvfile,))

        # INSERT races
        for racename,raceC in sorted(sheet.raceLut.items(),key=lambda x: x[0]):
            cur.execute('INSERT INTO race VALUES (?,?,?)',
                        (None, sheet.voteFor[racename], racename))
            raceId = cur.lastrowid
            self.raceLut[raceC] = raceId
            #!print('DBG: INSERT (race_id, votesAllowed, title) = ({},{},{})'
            #!      .format(rid, sheet.voteFor[racename], racename))
            #@@@ self.insert_fixed_choices(raceId, choiceInvLut)
        # INSERT choices, cvr, vote
        for r in range(sheet.minDataR, sheet.max_row + 1):
            cvr_id = cells[r][1]
            precinct = cells[r][2]
            ballot = cells[r][3]

            cur.execute('INSERT INTO cvr VALUES (?,?,?)',
                        (cvr_id, precinct, ballot))
            #logging.debug('INSERT cvr: {}'.format(cvr_id))

            for c in range(sheet.minDataC, sheet.max_col + 1):
                race_id = self.raceLut[sheet.raceLut[cells[1][c]]]
                choice_title = cells[r].get(c,None)
                if choice_title == None: continue

                if (race_id,choice_title) not in choiceInvLut:
                    cur.execute('INSERT INTO choice VALUES (?,?,?)',
                                (None, choice_title, race_id))
                    choice_id = cur.lastrowid
                    choiceInvLut[(race_id,choice_title)] = choice_id
                    
                cur.execute('INSERT INTO vote VALUES (?,?)',
                            (cvr_id, choiceInvLut[(race_id,choice_title)]))
        #! print('Added CSV ({}) content to LVR database {}'
        #!       .format(csvfile, self.dbfile))
        self.conn.commit()
        self.close_db()



##############################################################################

def main():
    "Parse command line arguments and do the work."
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    dfdb='LVR.db'
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
    #!logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    db = LvrDb(args.database)
    if args.incsv:
        args.incsv.close()
        args.incsv = args.incsv.name
        db.insert_from_csv(args.incsv)
        
    #!db.to_csv(foo)
    #!print('Created CSV from DB in {}'.format(foo))
    if args.summary:
        db.summary()
    
if __name__ == '__main__':
    main()
