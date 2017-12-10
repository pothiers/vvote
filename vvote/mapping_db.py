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
from difflib import SequenceMatcher
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
   lvr_race_title text,
   sovc_race_title text
);
CREATE TABLE choice_map (
   lvr_choice_title text,
   sovc_choice_title text
);'''


def gen_mapping(lvrdb, sovcdb, mapdb):
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
    lrc_lut = defaultdict(list) # lut[rid] => [cid, ...]
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

def printmap():
    pass
#!@    lvrfname = 'map_lvr.txt'
#!@    sovcfname = 'map_sovc.txt'
#!@    with open(lvrfname, 'w') as f:
#!@        for rid,rt in sorted(lr_lut.items(), key=lambda x: x[1]):
#!@            print('Race: {}'.format(rt), file=f)
#!@            for cid in lrc_lut[rid]:
#!@                print('  Choice: {}'.format(lc_lut[cid]), file=f)
#!@    with open(sovcfname, 'w') as f:
#!@        for rid,rt in sorted(sr_lut.items(), key=lambda x: x[1]):
#!@            print('Race: {}'.format(rt), file=f)
#!@            for cid in src_lut[rid]:
#!@                print('  Choice: {}'.format(sc_lut[cid]), file=f)
#!@
#!@    print('Wrote pretty map input to: {}, {}'.format(lvrfname,sovcfname))


def db2luts(con,sql):
    # Extract LUTS from DB
    r_lut = dict() # lut[id] => title
    c_lut = dict() # lut[id] => title
    rc_lut = defaultdict(list) # lut[rid] => [cid, ...]
    for (rid,rti,cid,cti) in con.execute(sql):
        r_lut[rid] = rti
        c_lut[cid] = cti
        rc_lut[rid].append(cid)
    return (r_lut,c_lut,rc_lut)

def rem_party(name):
    """Remove Party prefix from start of name."""
    party_prefixs = ['DEM ', 'REP ', 'GRN ', 'LBT ']

    if name[:4] in party_prefixs:
        return name[4:]
    else:
        return name

# Normalize differentces between LVR and SOVC choices
# LVR may contain unicode
def clean_choices(choices):
    """Normalize list of choices"""
    nukechars = str.maketrans(dict.fromkeys('()"'))
    repstrs = [
        #LVR        SOVC
        ('Á',        'A'),
        ('Í',        'I'),
        ('Ó',        'O'),
        ('Ú',        'U'),
        ('undervote', 'UNDER VOTES'),
        ('YES/SÍ',   'YES'),
        ('YES/Sí',   'YES'),
        ('YES/SI',   'YES'),
        ('Write-in', 'WRITE-IN'),
    ]

    choices = [rem_party(c) for c in choices]
    choices = [c.translate(nukechars) for c in choices]
    for (a,b) in repstrs: 
        choices = [c.replace(a,b) for c in choices]
    return sorted(choices)
    
def calc(mapdb):
    con = sqlite3.connect(mapdb)
    sql_tpl = '''SELECT 
  {src}_race.race_id     as rid,
  {src}_race.title       as rti,
  {src}_choice.choice_id as cid,
  {src}_choice.title     as cti
FROM {src}_race, {src}_choice, {src}_rc
WHERE {src}_rc.race_id = rid AND {src}_rc.choice_id = cid;'''
    sql_lvr = sql_tpl.format(src='lvr')
    sql_sovc = sql_tpl.format(src='sovc')

    # Extract LUTS from DB (for LVR and SOVC)
    #   r_lut[rid] => rti, c_lut[cid] => cti, rc_lut[rid] => [cid, ...]
    # LVR
    (lr_lut, lc_lut, lrc_lut) = db2luts(con, sql_lvr)
    lvr_lut = defaultdict(list) # lut[rti] => [cti, ...]
    for rid,rt in sorted(lr_lut.items(), key=lambda x: x[1]):
        lvr_lut[rt] = [lc_lut[cid] for cid in lrc_lut[rid]]
    # SOVC        
    (sr_lut, sc_lut, src_lut) = db2luts(con, sql_sovc)
    sovc_lut = defaultdict(list) # lut[rti] => [cti, ...]
    for rid,rt in sorted(sr_lut.items(), key=lambda x: x[1]):
        sovc_lut[rt] = [sc_lut[cid] for cid in src_lut[rid]]

    # Compare Races of LVR,SOVC
    iti = sorted(lvr_lut.keys())
    jti = sorted(sovc_lut.keys())
    s = SequenceMatcher(None, iti, jti)
    con.execute('DELETE from race_map;')
    for (tag, i1, i2, j1, j2) in s.get_opcodes():
        # ignore DELETE, INSERT cases.
        if tag in ['equal', 'replace']:
            assert i2-i1 == j2-j1, ('{} i2-i1 <> j2-j1 ({}-{}) <> ({}-{})'
                                    .format(tag,i2,i1,j2,j1))
            for offset in range(i2-i1):
                con.execute('INSERT INTO race_map VALUES (?,?)',
                            (iti[i1+offset], jti[j1+offset]))
        else:
            logging.warning('NOT creating LVR--SOVC race-map for: ({}) {}--{}'
                            .format(tag, iti[i1:i2], jti[j1:j2]))

    # Compare Choices of LVR,SOVC (single Choice list for each over ALL races)
    iti = clean_choices(lc_lut.values())
    jti = clean_choices(sc_lut.values())
    s = SequenceMatcher(None, iti, jti)
    #!pprint(('LVR  choices: ',iti))
    #!pprint(('SOVC choices: ',jti))
    #!pprint(s.get_opcodes())
    con.execute('DELETE from choice_map;')
    for (tag, i1, i2, j1, j2) in s.get_opcodes():
        # ignore DELETE, INSERT, REPLACE cases.
        if tag in ['equal',]:
            assert i2-i1 == j2-j1, ('{} i2-i1 <> j2-j1 ({}-{}) <> ({}-{})'
                                    .format(tag,i2,i1,j2,j1))
            for offset in range(i2-i1):
                con.execute('INSERT INTO choice_map VALUES (?,?)',
                            (iti[i1+offset], jti[j1+offset]))
        else:
            logging.warning('NOT creating LVR--SOVC choice-map for: ({}) {}--{}'
                            .format(tag, iti[i1:i2], jti[j1:j2]))

    # All done
    con.commit()
    con.close()
    return (lvr_lut, sovc_lut)


##############################################################################

def main():
    "Parse command line arguments and do the work."
    #print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    dfldb='LVR.db'
    dfsdb='SOVC.db'
    dfmdb='MAP.db'
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('--lvrdb', '-l', type=argparse.FileType('r'),
                        help='LVR sqlite DB')
    parser.add_argument('--sovcdb', '-s', type=argparse.FileType('r'),
                        help='SOVC sqlite DB')
    parser.add_argument('--mapdb', '-m', 
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
    if args.lvrdb:
        args.lvrdb.close()
        args.lvrdb = args.lvrdb.name
    if args.sovcdb:
        args.sovcdb.close()
        args.sovcdb = args.sovcdb.name


    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

        
    if args.lvrdb and args.sovcdb:
        print('Overwriting map data in "{}" from contents of "{}", "{}"'
              .format(args.mapdb, args.lvrdb, args.sovcdb))
        gen_mapping(args.lvrdb, args.sovcdb, args.mapdb)
    if args.calc:
        print('(re)Calculating mapping from map data')
        calc(args.mapdb)
    if args.pretty:
        print('Printing current mapping')
        printmap()
        
if __name__ == '__main__':
    main()



