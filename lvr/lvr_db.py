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
#################
## Python library
import sys
import argparse
import logging
import os
import os.path
import sqlite3
import csv
from collections import defaultdict
from pprint import pprint, pformat
import fileinput
#################
## External packages
#   (none)
#################
## LOCAL packages
import lvr.sql as sql
from lvr.lvr_sheet import LvrSheet

summary_msg = '''
LVR Database Summary:
   Sources: {} 
   Race count: {}
   Count (VoteFor,Choices) per race: \n{}
###################################################################
'''


class LvrDb():
    """Manage LVR Database (sqlite3 format)"""
    fixed_choices = ['overvote', 'undervote', 'Write-in']
    
    def __init__(self, dbfile):
        self.dbfile = dbfile
        self.conn = sqlite3.connect(dbfile)
        self.cur = self.conn.cursor()
        self.minDataC = 3  # Data COLUMN starts here (first column=0)

        self.raceColLut = dict() # lut[column] => raceId
        self.choiceInvLut = dict()# lut[(choicetitle, raceid)] = choiceid

    def new_db(self, overwrite=True):
        dbfile = self.dbfile
        if overwrite:
            if os.path.exists(dbfile):
                os.remove(dbfile)
                print('Removed LVR database: {}'.format(dbfile))
        self.conn = sqlite3.connect(dbfile)
        self.cur = self.conn.cursor()
        self.cur.executescript(sql.lvr_schema)
        print('Created schema in LVR database: {}'.format(dbfile))
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
        sourcefiles = [f for (f,) in cur.fetchall()]
        cur.execute(
            'SELECT num_to_vote_for,count(choice.race_id) FROM choice,race'
            ' WHERE choice.race_id = race.race_id'
            ' GROUP BY race.race_id ORDER BY race.race_id;')
        va_choice_list = [(int(r[0]),int(r[1])) for r in cur.fetchall()]
        print(summary_msg.format(', '.join(sourcefiles),
                                 len(va_choice_list),
                                 ','.join([str(v) for v in va_choice_list]),  ))

    def insertRaces(self, fieldnames):
        print('DBG: insertRaces();{}'.format(fieldnames))
        left = self.minDataC
        for column,racename in enumerate(fieldnames[left:],left):
            if len(racename.strip()) == 0:
                continue
            voteFor = 1
            for f in fieldnames[column+1:]: 
                if f.strip() == '':
                    voteFor += 1
                else:
                    break
            self.cur.execute('INSERT INTO race VALUES (?,?,?,?)',
                        (None,  racename, column, voteFor))
            raceId = self.cur.lastrowid
            self.raceColLut[column] = raceId
        

    def insert_LVR_from_csv_files(self,csvfile_list, progress=10000):
        """Append to existing Sqlite DB.
   CSV format (per G2016 results; 'day-1-cvr.csv') VERY SPARSE in places!

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
        if len(csvfile_list) > 0:
            self.new_db()
        fi = fileinput.FileInput(files=csvfile_list)

        with fi as csvfile: # csvfile is each openfile in order
            reader = csv.reader(csvfile, dialect='excel')
            
            # rid:: rowId; cid:: columnId
            for row in reader:
                if 0 == (fi.lineno() % progress):
                    print('Ballots processed = {}'.format(fi.lineno()))
                if 1 == fi.lineno():
                    fieldnames = row
                    self.insertRaces(fieldnames)
                    continue
                if 2 == fi.filelineno():
                    print('Adding CSV ({}) content to LVR database {}'
                          .format(fi.filename(),self.dbfile))
                    #!print('DBG: header={}'.format(fieldnames))
                    self.cur.execute('INSERT INTO source VALUES (?)',
                                     (fi.filename(),))
                if fi.isfirstline():
                    continue # skip hdr line (first hdr read before loop)

                (cvr_id, precinct, ballot) = row[:self.minDataC]
                try:
                    self.cur.execute('INSERT INTO cvr VALUES (?,?,?)',
                                     (cvr_id, precinct, ballot))
                except Exception as err:
                    print('ERROR: could not insert into cvr ({},{},{}); {}'
                          .format(cvr_id, precinct, ballot, err))
                    sys.exit()
                    
                datarow = row[self.minDataC:]
                for (column, choice_title) in enumerate(datarow,self.minDataC):
                    try:
                        race_id = self.raceColLut[column]
                    except:
                        pass # use previous race_id on blank column header

                    if (choice_title,race_id) not in self.choiceInvLut:
                        self.cur.execute('INSERT INTO choice VALUES (?,?,?,?)',
                                         (None, choice_title, race_id, 'NA'))
                        choice_id = self.cur.lastrowid
                        self.choiceInvLut[(choice_title,race_id)] = choice_id
                    self.cur.execute(
                        'INSERT INTO vote VALUES (?,?)',
                        (cvr_id, self.choiceInvLut[(choice_title,race_id)]))
        fi.close()
        #!self.conn.commit()
        self.close_db()
    # END: insert_LVR_from_csv_files()



        

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
    db.insert_LVR_from_csv_files(args.LVRfiles)
        
    if args.summary:
        db.summary()
    
if __name__ == '__main__':
    main()
