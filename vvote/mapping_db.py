#! /usr/bin/env python
"""Creating mapping between Race and Choice strings in LVR and SOVC.

EXAMPLES:
  makemapdb LVR.db SOVC.db -m MAP.db
"""

# Docstrings intended for document generation via pydoc

import sys
import argparse
import logging
import os
import os.path
import sqlite3
from collections import defaultdict
from pprint import pprint

##############################################################################
### Database
###

map_schema = '''
CREATE TABLE source (
   map_filename text,
   lvr_filename text,
   sovc_filename text
);

-- LVR
CREATE TABLE lvr_race (
   race_id integer primary key,
   title text
);
CREATE TABLE lvr_choice (
   choice_id integer primary key,
   title text
);
CREATE TABLE lvr_rc (
   race_id integer,
   choice_id integer
);

-- SOVC
CREATE TABLE sovc_race (
   race_id integer primary key,
   title text
);
CREATE TABLE sovc_choice (
   choice_id integer primary key,
   title text
);
CREATE TABLE SOVC_rc (
   race_id integer,
   choice_id integer
);

-- MAP
CREATE TABLE race_map (
   lvr_race_id integer,
   sovc_race_id integer
);
CREATE TABLE choice_map (
   lvr_choice_id integer,
   sovc_choice_id integer
);'''


def gen_mapping(lvrdb, sovcdb, mapdb, pretty=True):
    if os.path.exists(mapdb):
        os.remove(mapdb)
    conmap = sqlite3.connect(mapdb)
    conmap.executescript(map_schema)
    conmap.execute('INSERT INTO source VALUES (?,?,?)',
                   (mapdb, lvrdb, sovcdb))

    # LVR: Insert Race,Choice info 
    conlvr = sqlite3.connect(lvrdb)
    lvr_rc_sql = '''SELECT DISTINCT 
  race.title AS rt, 
  race.race_id AS rid, 
  choice.title AS ct,
  choice.choice_id AS cid
FROM vote,race,choice 
WHERE vote.race_id = race.race_id AND vote.choice_id = choice.choice_id 
ORDER BY rt, ct;'''
    lrc_lut = defaultdict(list) # rc[rid] => [cid, ...]
    lr_lut = dict() # lut[id] => title
    lc_lut = dict() # lut[id] => title
    for (rt,rid,ct,cid) in conlvr.execute(lvr_rc_sql):
        lrc_lut[rid].append(cid)
        lr_lut[rid] = rt
        lc_lut[cid] = ct
    for id,t in lr_lut.items():
        conmap.execute('INSERT INTO lvr_race VALUES (?,?)',(id, t))
    for id,t in lc_lut.items():
        conmap.execute('INSERT INTO lvr_choice VALUES (?,?)',(id, t))
    for rid in lrc_lut.keys():
        for cid in lrc_lut[rid]:
            conmap.execute('INSERT INTO lvr_rc VALUES (?,?)',(rid,cid))

    # SOVC: Insert Race,Choice info 
    consovc = sqlite3.connect(sovcdb)
    sovc_rc_sql = '''SELECT DISTINCT 
  race.title AS rt, 
  race.race_id AS rid, 
  choice.title AS ct,
  choice.choice_id AS cid 
FROM precinct,race,choice 
WHERE precinct.race_id = race.race_id AND precinct.choice_id = choice.choice_id 
ORDER BY rt, ct;'''
    src_lut = defaultdict(list) # rc[rid] => [cid, ...]
    sr_lut = dict() # lut[id] => title
    sc_lut = dict() # lut[id] => title
    for (rt,rid,ct,cid) in consovc.execute(sovc_rc_sql):
        src_lut[rid].append(cid)
        sr_lut[rid] = rt
        sc_lut[cid] = ct
    for id,t in sr_lut.items():
        conmap.execute('INSERT INTO sovc_race VALUES (?,?)',(id, t))
    for id,t in sc_lut.items():
        conmap.execute('INSERT INTO sovc_choice VALUES (?,?)',(id, t))
    for rid in src_lut.keys():
        for cid in src_lut[rid]:
            conmap.execute('INSERT INTO sovc_rc VALUES (?,?)',(rid,cid))
    
    conmap.commit()
    conmap.close()
    if pretty:
        lvrfname = 'map_lvr.txt'
        sovcfname = 'map_sovc.txt'
        with open(lvrfname, 'w') as f:
            for rid,rt in sorted(lr_lut.items(), key=lambda x: x[1]):
                print('Race: {}'.format(rt), file=f)
                for cid in lrc_lut[rid]:
                    print('  Choice: {}'.format(lc_lut[cid]), file=f)
        with open(sovcfname, 'w') as f:
            for rid,rt in sorted(sr_lut.items(), key=lambda x: x[1]):
                print('Race: {}'.format(rt), file=f)
                for cid in src_lut[rid]:
                    print('  Choice: {}'.format(sc_lut[cid]), file=f)

        print('Wrote pretty map input to: {}, {}'.format(lvrfname,sovcfname))

def printmap():
    pass

def calc():
    pass

##############################################################################

def main():
    "Parse command line arguments and do the work."
    #print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    dfmdb='MAP.db'
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('lvrdb', type=argparse.FileType('r'),
                        help='LVR sqlite DB')
    parser.add_argument('sovcdb', type=argparse.FileType('r'),
                        help='SOVC sqlite DB')
    parser.add_argument('--mapdb', '-m', type=argparse.FileType('w'),
                        default=dfmdb,
                        help='MAP sqlite DB')

    parser.add_argument('--calc', '-c', action='store_true',
                        help='Calculating mapping (and store in db)')
    parser.add_argument('--pretty', '-p', action='store_true',
                        help='Pretty-print mapping')
    
    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING')
    args = parser.parse_args()
    args.lvrdb.close()
    args.lvrdb = args.lvrdb.name
    args.sovcdb.close()
    args.sovcdb = args.sovcdb.name
    args.mapdb.close()
    args.mapdb = args.mapdb.name


    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

        
    if args.mapdb:
        print('Overwriting map data in {} from contents of {}, {}'
              .format(args.mapdb, args.lvrdb, args.sovcdb))
        gen_mapping(args.lvrdb, args.sovcdb, args.mapdb)
    if args.calc:
        print('(re)Calculating mapping from map data')
        calc()
    if args.pretty:
        print('Printing current mapping')
        printmap()
        
if __name__ == '__main__':
    main()



