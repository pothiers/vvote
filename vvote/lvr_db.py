#! /usr/bin/env python
"""Manage LVR database.
- Load from Official ballots file(s). Named *LVR*.xlsx or *CVR*.xlsx
- Export as CSV. 

LVR :: List of CVR records (an excel file, each row is CVR except
     header row=1) Each record is the ballot results from one person.

Underlying dimensionality of LVR Data (value is Choice(string)):
1. CVR
2. Race
"""

import sys
import argparse
import logging
import csv
import os
import os.path
import sqlite3
from collections import defaultdict
import pprint

##############################################################################
### Database
###

lvr_schema = '''
CREATE TABLE source (
   filename text
);
CREATE TABLE race (
   race_id integer primary key,
   votesAllowed integer,
   title text
);
CREATE TABLE choice (
   choice_id integer primary key,
   title text
);
CREATE TABLE cvr (
   cvr_id integer primary key,
   precinct_code,
   ballot_style text
);
CREATE TABLE vote (
   cvr_id integer,
   race_id integer,
   choice_id integer
);
'''

class LvrDb():
    """Manage LVR Database (sqlite3 format)"""

    dbfile = None
    sourcefile = None

    def __init__(self, dbfile):
        self.dbfile = dbfile
        self.new_db(dbfile, overwrite=True)
    

    def new_db(self, dbfile, overwrite=True):
        if overwrite:
            if os.path.exists(dbfile):
                os.remove(dbfile)

        self.conn = sqlite3.connect(dbfile)
        cur = self.conn.cursor()
        cur.executescript(lvr_schema)

    def insert_from_csv(self,csvfile):
        """Append to existing Sqlite DB."""
        sheet = LvrSheet(csvfile)
        sheet.summary()
        
        cur = self.conn.cursor()
        cells = sheet.cells
        cur.execute('INSERT INTO source VALUES (?)', (csvfile,))
        choices = set() # of choice_id

        # INSERT races
        for racename,rid in sorted(sheet.raceLut.items(),key=lambda x: x[0]):
            cur.execute('INSERT INTO race VALUES (?,?,?)',
                        (rid, sheet.voteFor[racename], racename))
        # INSERT choices, cvr, vote
        for r in range(sheet.minDataR, sheet.max_row + 1):
            cvr_id = cells[r][1]
            precinct = cells[r][2]
            ballot = cells[r][3]

            cur.execute('INSERT INTO cvr VALUES (?,?,?)',
                        (cvr_id, precinct, ballot))
            #logging.debug('INSERT cvr: {}'.format(cvr_id))

            for c in range(sheet.minDataC, sheet.max_col + 1):
                race_id = sheet.raceLut[cells[1][c]]
                choice_title = cells[r].get(c,None)
                if choice_title: # not blank
                    choice_id = sheet.choiceLut[choice_title]
                    #!logging.debug('cells[{},{}] = {} [{}]'.
                    #!              format(r,c,cells[r][c], choice_id))
                    if choice_id not in choices:
                        choices.add(choice_id)
                        cur.execute('INSERT INTO choice VALUES (?,?)',
                                    (choice_id, cells[r][c]))
                    cur.execute('INSERT INTO vote VALUES (?,?,?)',
                                (cvr_id, race_id, choice_id))

        self.conn.commit()
        self.conn.close()


                
        

### end LvrDb
##############################################################################

##############################################################################
### Spreadsheet
###
class LvrSheet():
    """CSV format (per G2016 results; 'day-1-cvr.csv')
 VERY SPARSE in places!

   Row 1:: Headers
     Col 1:: "Cast Vote Record"
     Col 2:: "Precinct"
     Col 3:: "Ballot Style"
     Col 4 to M: RaceName 
        May be blank for VoteFor > 1; treat as RaceName from left non-blank

   Row N::
     Col 1:: CVR (integer)
     Col 2:: Precinct (integer)
     Col 3:: Ballot Style (text)
     Col 4 to M: ChoiceName (corresponding to RaceName in Row 1)
"""
    filename = ''
    cells = defaultdict(dict) # cells[row][column] => value
    max_row = 0
    max_col = 0
    minDataC = 4  # Data COLUMN starts here
    minDataR = 2  # Data ROW starts here
    raceLut = dict() # lut[raceName] = columnNumber (left col of race)
    choiceLut = dict() # lut[choiceName] = id
    voteFor = dict() # lut[raceName] = numberToVoteFor

    def __init__(self, filename):
        """RETURN: sparse 2D matrix representing spreadsheet"""
        self.filename = filename
        choice_id = 0
        with open(filename, newline='') as csvfile:
            reader = csv.reader(csvfile, dialect='excel')
            for rid,row in enumerate(reader, 1):
                for cid,val in enumerate(row,1):
                    value = val.strip()
                    if len(value) > 0:
                        self.cells[rid][cid] = value
                        if ((rid >= self.minDataR)  and (cid >= self.minDataC)
                            and (value not in self.choiceLut)):
                            self.choiceLut[value] = choice_id
                            choice_id += 1
                        #!else:
                        #!    logging.debug('Already saw choice: "{}"'
                        #!                  .format(value))
                        self.max_col = max(self.max_col, cid)
                if (rid >= self.minDataR) and (len(self.cells[rid]) >= self.minDataC):
                    self.max_row = rid
        # Fill RaceName for VoteFor > 1
        raceName = None
        for c in range(self.minDataC, self.max_col + 1):
            if c in self.cells[1]:
                raceName = self.cells[1][c]
                self.voteFor[raceName] = 1
                self.raceLut[raceName] = c
            else:
                self.cells[1][c] = raceName
                self.voteFor[raceName] += 1
        # END: init

    def summary(self):
        vals = sorted(self.choiceLut.values())
        print('''
Sheet Summary:
   FILENAME: {} # CSV source
   minDataR: {:2}  Max ROW:  {}
   minDataC: {:2}  Max COL:  {}
   Cell cnt: {}

   Race cnt:     {}
   VoteFor cnts: {}
   Choice cnt:   {}
   choice ids: {} ... {}
###################################################################
'''
              .format(self.filename,
                      self.minDataR, self.max_row, 
                      self.minDataC, self.max_col, 
                      sum([len(v) for v in self.cells.values()]),
                      len(self.raceLut),
                      ','.join([str(v) for v in self.voteFor.values()]),
                      len(self.choiceLut),
                      vals[:4], vals[len(vals)-4:],
              ))


###
### end LvrSheet
##############################################################################
    



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

    parser.add_argument('infile', type=argparse.FileType('r'),
                        help='Input CSV file')
    parser.add_argument('-d', '--database', type=argparse.FileType('w'),
                        default=dfdb,
                        help=('SQlite database file to hold content.'
                              '  [default="{}"]').format(dfdb))

    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING')
    args = parser.parse_args()
    args.database.close()
    args.database = args.database.name
    args.infile.close()
    args.infile = args.infile.name


    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    #!logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    db = LvrDb(args.database)
    db.insert_from_csv(args.infile)
    print('Inserted data from {} into {}'.format(args.infile, args.database))
    #!foo = 'foo-lvr.csv'
    #!db.to_csv(foo)
    #!print('Created CSV from DB in {}'.format(foo))
    
if __name__ == '__main__':
    main()
