#! /usr/bin/env python
"""Manage SOVC database.
- Load from Official Election Results excel file(s).
- Export as CSV. 

SOVC :: Statement Of Votes Cast; official election results
"""
# Docstrings intended for document generation via pydoc

import sys
import argparse
import logging
import csv
import os
import os.path
import sqlite3
from collections import defaultdict
import pprint

sovc_schema = '''
CREATE TABLE source (
   filename text
);
CREATE TABLE race (
   race_id integer primary key,
   title text,
   num_to_vote_for integer
);
CREATE TABLE choice (
   choice_id integer primary key,
   title text,
   race_id integer,
   party text
);
CREATE TABLE precinct (
  race_id integer,
  choice_id integer,
  county_number,
  precinct_code,  -- id
  precinct_name,
  registered_voters integer,
  ballots_cast_total integer,
  ballots_cast_blank integer
);
CREATE TABLE vote (
  choice_id integer,
  precinct_code,
  count integer
);
'''

class SovcDb():
    """Manage SOVC Database (sqlite3 format)"""
    def __init__(self, dbfile, sourcesheet):
        self.sourcesheet = sourcesheet
        self.dbfile = dbfile
        self.new_db(dbfile, sourcesheet.filename)
        

    def new_db(self, dbfile, sourcefile):
        self.source = sourcefile
        if os.path.exists(dbfile):
            os.remove(dbfile)

        # create new file
        self.conn = sqlite3.connect(dbfile)
        cur = self.conn.cursor()
        cur.executescript(sovc_schema)
        cur.execute('INSERT INTO source VALUES (?)', (sourcefile,))

    def insert_race_list(self, race_list):
        """race_list:: [(race_id, title, num_to_vote_for), ...]"""
        cur = self.conn.cursor()
        cur.executemany('INSERT INTO race VALUES (?,?,?)', race_list)
        
    def insert_choice_list(self, choice_list):
        """choice_list:: [(choice_id, title, race_id, party), ...]"""
        cur = self.conn.cursor()
        cur.executemany('INSERT INTO choice VALUES (?,?,?,?)', choice_list)
        
    def insert_precinct_list(self, precinct_list):
        """
        precinct_list::
        [(race_id, 
          choice_id,
          county_number,
          precinct_code,
          precinct_name,
          num_registered_voters,
          ballots_cast_total,
          ballots_cast_blank,
          ), ...]"""
        #!print('DBG: precinct_list=')
        #!pprint.pprint(precinct_list)
        cur = self.conn.cursor()
        cur.executemany('INSERT INTO precinct VALUES (?,?,?,?,?,?,?,?)',
                        precinct_list)
    
    def insert_vote_list(self, vote_list):
        """vote_list:: [(choice_id, precinct_code, count), ...]"""
        cur = self.conn.cursor()
        cur.executemany('INSERT INTO vote VALUES (?,?,?)', vote_list)
        
    def close(self):
        self.conn.commit()
        self.conn.close()

class SovcSheet():
    """CSV format (per Nov-2017 results; '171107C_EXPORT DAY 2.CSV')
   Row 1:: Race titles (duplicated over columns representing choices)
   Row 2:: party (we don't care)
   Row 3:: Choices
   Row 4 to N-1:: Precinct totals
   Row N:: Grand totals (County totals)
   Row N+1:: "_x001A_"  ??? End of data?

   Col 1:: County Number ('_x001A_' in last row)
   Col 2:: Precinct Code (number)
   Col 3:: Precinct Name (number) or "COUNTY TOTALS"
   Col 4:: "REGISTERED VOTERS - TOTAL" (Row 1)
   Col 5:: Ballots Cast-Total
   Col 6:: Ballots Cast-Blank
   Col 7 to M:: vote counts
"""
    filename = ''
    cells = defaultdict(dict) # cells[row][column] => value
    max_row = 0
    max_col = 0
    minDataC = 7

    def __init__(self, filename):
        """RETURN: sparse 2D matrix representing spreadsheet"""
        self.filename = filename
        with open(filename, newline='') as csvfile:
            sovcreader = csv.reader(csvfile, dialect='excel')
            for rid,row in enumerate(sovcreader, 1):
                for cid,val in enumerate(row,1):
                    value = val.strip()
                    if len(value) > 0:
                        self.cells[rid][cid] = value
                        self.max_col = max(self.max_col, cid)
                self.max_row = rid
        #print('CELLS={}'.format(pprint.pformat(self.cells, indent=3)))
        # END: init

    def summary(self):
        print('''
Sheet Summary:
   filename: {}
   Max ROW:  {}
   Max COL:  {}
   minDataC: {}
   Cell cnt: {}'''
              .format(self.filename, self.max_row, self.max_col, self.minDataC,
                      sum([len(v) for v in self.cells.values()])))

    

    def get_race_lists(self):
        logging.debug('DBG: get RACE and CHOICE lists')
        choiceLut = dict()   # lut[title] = id
        raceLut = dict()     # lut[title] = id
        race_list = list()   # [(rid, racetitle, numToVoteFor), ...]
        choice_list = list() # [(cid, choicetitle, party), ...]
        c1 = self.minDataC
        while c1 <= self.max_col:
            rid = c1
            #print('c={}, cells[1]={}'.format(c, self.cells[1]))
            racetitle = self.cells[1][c1]
            logging.debug('Racetitle={}'.format(racetitle))
            race_list.append((rid, racetitle, None))
            raceLut[racetitle] = rid
            for c2 in range(c1, self.max_col+1):
                cid = c2
                if racetitle == self.cells[1][c2]:
                    choicetitle = self.cells[3][c2]
                    logging.debug('Choicetitle={}'.format(choicetitle))
                    choice_list.append((cid, choicetitle, rid, None))
                    choiceLut[choicetitle] = cid
                else:
                    break
            c1 = cid + 1 if (racetitle != self.cells[1][c2]) else cid
        logging.debug('Race cnt={}, Choice cnt={}'

                      .format(len(race_list), len(choice_list)))
        return race_list, choice_list
        
    def get_precinct_votes(self):
        "RETURN: dict[(race,choice)] => (count,precinct,regvot,baltot,balblank)"
        logging.debug('DBG: get PRECINCT and VOTE lists')

        races = [self.cells[1][c]
                 for c in range(self.minDataC, self.max_col+1)]
        choices = [self.cells[3][c]
                   for c in range(self.minDataC, self.max_col+1)]
        totdict = dict() 
        logging.debug('DBG: races({}) = {}'.format(len(races), races))
        logging.debug('DBG: choices({}) = {}'.format(len(choices), choices))

#!        for r,row in enumerate(self.ws.rows, start=1):
#!            (county,pcode,precinct,numreg,btotal,bblank,*tally) = row
#!            for c,cell in enumerate(row): #columns
#!                logging.debug('c={}'.format(c))
#!                if cell.value == None: continue
#!                race = races[c]
#!                choice = choices[c]
#!                if race == None or choice == None: continue
#!                totdict[(race, choice)] = ( cell.value,
#!                    precinct.value, numreg.value, btotal.value, bblank.value)
#!
#!        #return totdict
#!        
#!        precinct_list = list() 
#!        vote_list = list()     # [(cid, precinct_code, count), ...]
#!        # dict[(race,choice] => (count,precinct,regvot,baltot,balblank)"
#!        pt = self.get_precinct_totals()
#!        for ((racetitle,choicetitle),
#!             (count,precinct,regvot,baltot,balblank)) in pt.items():
#!            choice_id = choiceLut.get(choicetitle, None)
#!            precinct_list.append((raceLut[racetitle],
#!                                  choice_id,
#!                                  None, # county_number
#!                                  precinct,
#!                                  precinct,
#!                                  regvot, # registered_voters integer,
#!                                  baltot, # ballots_cast_total integer,
#!                                  balblank # ballots_cast_blank integer
#!                                  ))
#!            vote_list.append((choice_id, precinct, count))

        

def csv_to_db(csvfile, sqlite_file):
    """Append to existing Sqlite DB (or create new one).
"""
    sovcsheet = SovcSheet(csvfile.name)
    sovcsheet.summary()
    sovcdb = SovcDb(sqlite_file, sovcsheet)

    (race_list, choice_list) = sovcsheet.get_race_lists()
    sovcdb.insert_race_list(race_list)
    sovcdb.insert_choice_list(choice_list)

    #!(precinct_list, vote_list) = sovcsheet.get_precinct_votes()
    #!sovcdb.insert_precinct_list(precinct_list)        
    #!sovcdb.insert_vote_list(vote_list)        

    sovcdb.close()
    logging.debug('DBG: Created RACE and CHOICE tables in {}'
                  .format(sqlite_file))
    


##############################################################################

def main():
    "Parse command line arguments and do the work."
    #print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    dfdb='SOVC.db'
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

    #!print 'My args=',args
    #!print 'infile=',args.infile

    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    csv_to_db(args.infile, args.database)
    
if __name__ == '__main__':
    main()
