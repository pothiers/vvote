#! /usr/bin/env python
"""Manage SOVC database.
- Load from Official Election Results excel file(s).
- Export as CSV. 

SOVC :: Statement Of Votes Cast; official election results

Underlying dimensionality of SOVC Data (value is count-of-votes):
1. County
2. Precinct
3. Race
4. Choice
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

##############################################################################
### Database
###

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

    # OUTPUT: Race, NumToVoteFor, Choice, ChoiceId, ...
    def to_csv(self,csv_filename):
        self.conn = sqlite3.connect(self.dbfile)
        cur = self.conn.cursor()
        
        choice_sql = '''SELECT 
  race.title AS rt,   
  race.num_to_vote_for as nv,
  choice.title AS ct,  
  choice.choice_id as cid
FROM choice, race
WHERE race.race_id = choice.race_id 
ORDER BY race_id ASC, choice_id ASC;'''

        sql_precinct = '''SELECT 
  precinct.county_number AS county,
  precinct.precinct_code AS pcode,
  precinct.precinct_name AS pname,
  precinct.registered_voters AS totvot,
  precinct.ballots_cast_total AS totbal,
  precinct.ballots_cast_blank AS blankbal,
FROM precinct 
ORDER BY precinct.county_number ASC, pcode ASC;'''

        sql_race = '''SELECT vote.count AS count
FROM vote, precinct
WHERE vote.precinct_code = precinct.precinct_code
ORDER BY race_id
;
'''

        rc_list = [(row['rt'], row['ct'], row['cid'])
                   for row in cur.execute(choice_sql)]
        headers1 = ('COUNTY NUMBER,PRECINCT CODE,PRECINCT NAME,'
                    'REGISTERED VOTERS - TOTAL,BALLOTS CAST - TOTAL,'
                    'BALLOTS CAST - BLANK').split(',')
        headers1.extend([r for r,nv,c,cid in rc_list])        
        headers2 = ['Number to Vote For ->', '','','','','']
        headers2.extend([nv for r,nv,c,cid in rc_list])
        headers3 = ['Choice ->', '','','','','']
        headers3.extend([c for r,nv,c,cid in rc_list])
        
        fns = 'county,pcode,pname,totvot,totbal,blankbal'.split(',')
        fns.extend([c for r,c in rc_list])
        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, dialect='excel')
            writer.writerow(headers1)
            writer.writerow(headers2)
            writer.writerow(headers3)
            # loop over:
            #   Precinct (by County/Precinct),
            #   Race+Choice (by Race/Choice
            for row in cur.execute(sql_precinct):
                c6 = [row['county'], row['pcode'], row['pname'],
                      row['totvot'], row['totbal'],row['blankbal']]
                votes_list = list()
                for row in cur.execute(sql_race): # for one precinct
                    votes_list.append(row['count'])
                writer.writerow(c6 + votes_list)
            

### end SovcDb
##############################################################################

##############################################################################
### Spreadsheet
###

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
    minDataC = 7  # Data COLUMN starts here
    minDataR = 4  # Data ROW starts here
    choiceLut = dict() # lut[title] = columnNumber
    raceLut = dict() # lut[title] = columnNumber

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
                #logging.debug('DBG: cells[rid]={}'.format(self.cells[rid]))
                if (rid >= self.minDataR) and (len(self.cells[rid]) > 4):
                    self.max_row = rid
        #print('CELLS={}'.format(pprint.pformat(self.cells, indent=3)))
        # END: init

    def summary(self):
        print('''
Sheet Summary:
   filename: {}

   Max ROW:  {}
   minDataR: {}
   Max COL:  {}
   minDataC: {}
   Cell cnt: {}

   Race cnt:   {}
   Choice cnt: {}
'''
              .format(self.filename,
                      self.max_row, self.minDataR,
                      self.max_col, self.minDataC,
                      sum([len(v) for v in self.cells.values()]),
                      len(self.raceLut), len(self.choiceLut),
              ))

    def get_race_lists(self):
        logging.debug('Get RACE and CHOICE lists')
        race_list = list()   # [(rid, racetitle, numToVoteFor), ...]
        choice_list = list() # [(cid, choicetitle, party), ...]
        c1 = self.minDataC
        while c1 <= self.max_col:
            rid = c1
            racetitle = self.cells[1][c1]
            logging.debug('Racetitle={}'.format(racetitle))
            race_list.append((rid, racetitle, None))
            self.raceLut[racetitle] = rid
            for c2 in range(c1, self.max_col+1):
                #!logging.debug('c1={}, c2={}'.format(c1,c2))
                cid = c2
                if racetitle == self.cells[1][c2]:
                    choicetitle = self.cells[3][c2]
                    #!logging.debug('Choicetitle={}'.format(choicetitle))
                    choice_list.append((cid, choicetitle, rid, None))
                    self.choiceLut[choicetitle] = cid
                else:
                    cid -= 1
                    break
            c1 = cid + 1 
        logging.debug('Race cnt={}, Choice cnt={}'
                      .format(len(race_list), len(choice_list)))
        return race_list, choice_list
        
    def get_precinct_votes(self):
        "RETURN: dict[(race,choice)] => (count,precinct,regvot,baltot,balblank)"
        logging.debug('Get PRECINCT and VOTE lists')

        precinct_list = list() # [(race_id, choice_id, county, pcode, pname,
                               # regvot, baltot, balblank), ...]
        vote_list = list()     # [(cid, precinct_code, count), ...]
        for col in range(self.minDataC, self.max_col+1):
            racetitle = self.cells[1][col]
            race_id = self.raceLut[racetitle]
            choicetitle = self.cells[3][col]
            choice_id = self.choiceLut[choicetitle]
            for row in range(self.minDataR, self.max_row+1):
                precinct_list.append(
                    (race_id,
                     choice_id,
                     self.cells[row][1],   # county number
                     self.cells[row][2],   # precinct code
                     self.cells[row][3],   # precinct name
                     self.cells[row][4],   # reg voters total
                     self.cells[row][5],   # ballots total
                     self.cells[row][6]    # ballots blank
                    ))
                vote_list.append(
                    (choice_id,
                     self.cells[row][2],
                     self.cells[row][col] # vote count
                    ))
        return (precinct_list, vote_list)

###
### end SovcSheet
##############################################################################


def csv_to_db(csvfile, sqlite_file):
    """Append to existing Sqlite DB (or create new one).
"""
    sovcsheet = SovcSheet(csvfile.name)
    sovcdb = SovcDb(sqlite_file, sovcsheet)

    (race_list, choice_list) = sovcsheet.get_race_lists()
    sovcdb.insert_race_list(race_list)
    sovcdb.insert_choice_list(choice_list)

    (precinct_list, vote_list) = sovcsheet.get_precinct_votes()
    #logging.debug('DBG: precinct_list={}'.format(precinct_list))
    sovcdb.insert_precinct_list(precinct_list)        
    sovcdb.insert_vote_list(vote_list)        

    sovcdb.close()
    logging.debug('DBG: Created RACE and CHOICE tables in {}'
                  .format(sqlite_file))

    sovcsheet.summary()



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
