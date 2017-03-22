import sqlite3
import os
import os.path
import pprint


schema = '''
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

class BallotDb():
    def __init__(self, dbfile, sourcefile):
        if os.path.exists(dbfile):
            os.remove(dbfile)

        # create new file
        self.conn = sqlite3.connect(dbfile)
        cur = self.conn.cursor()
        cur.executescript(schema)
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
        
