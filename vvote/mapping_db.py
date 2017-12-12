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
import copy

from . import sql

##############################################################################
### Database
###


def gen_mapping(lvrdb, sovcdb, mapdb):
    if os.path.exists(mapdb):
        os.remove(mapdb)
    conmap = sqlite3.connect(mapdb)
    conmap.executescript(sql.map_schema)
    conmap.execute('INSERT INTO source VALUES (?,?,?)',
                   (mapdb, lvrdb, sovcdb))

    # LVR: Insert Race,Choice info 
    conlvr = sqlite3.connect(lvrdb)
    lrc_lut = defaultdict(list) # lut[rid] => [cid, ...]
    lr_lut = dict() # lut[id] => title
    lc_lut = dict() # lut[id] => title
    for (rt,rid,ct,cid) in conlvr.execute(sql.map_lvr_rc):
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
    src_lut = defaultdict(list) # rc[rid] => [cid, ...]
    sr_lut = dict() # lut[id] => title
    sc_lut = dict() # lut[id] => title
    for (rt,rid,ct,cid) in consovc.execute(sql.map_sovc_rc):
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
def clean_choices(lut):
    """Normalize dict of choices.
lut[cid] => ctitle
RETURN: [(cid,title), ...];  Sorted by TITLE.
"""
    newlut = copy.copy(lut) # newlut[cid] => title
    nukechars = str.maketrans(dict.fromkeys('()"'))
    repstrs = [
        #LVR        SOVC
        ('Á',        'A'),
        ('Í',        'I'),
        ('Ó',        'O'),
        ('Ú',        'U'),
        ('overvote', 'OVER VOTES'),
        ('undervote','UNDER VOTES'),
        ('YES/SÍ',   'YES'),
        ('YES/Sí',   'YES'),
        ('YES/SI',   'YES'),
        ('Write-in', 'WRITE-IN'),
    ]

    for k in lut.keys():
        newlut[k] = rem_party(newlut[k])
        newlut[k] = newlut[k].translate(nukechars)
        for (a,b) in repstrs:
            newlut[k] = newlut[k].replace(a,b)
    return sorted(newlut.items(), key=lambda x: x[1])

def calc(mapdb, acceptAllReplacement=True):
    con = sqlite3.connect(mapdb)
    sql_lvr = sql.map_tpl.format(src='lvr')
    sql_sovc = sql.map_tpl.format(src='sovc')

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

    ##########################################################
    ### Compare Races of LVR,SOVC
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
            print('\nNOT creating LVR--SOVC race-map for: ({}) {}--{}'
                  .format(tag, iti[i1:i2], jti[j1:j2]))

    ##########################################################
    ### Compare Choices of LVR,SOVC (single Choice list for each over ALL races)
    # create cleaned CID-list, CTitle-list (for LVR and SOVC)
    iid,iti = zip(*clean_choices(lc_lut))
    jid,jti = zip(*clean_choices(sc_lut))
    s = SequenceMatcher(None, iti, jti)
    #! pprint(('LVR  choices: ',iti))
    #! pprint(('SOVC choices: ',jti))
    #! pprint(s.get_opcodes())
    con.execute('DELETE from choice_map;')
    for (tag, i1, i2, j1, j2) in s.get_opcodes():
        # Possible tags: equal, delete, insert, replace
        ispan = i2-i1
        jspan = j2-j1
        if tag == 'equal':
            assert ispan == jspan, ('{} i2-i1 <> j2-j1 ({}-{}) <> ({}-{})'
                                    .format(tag,i2,i1,j2,j1))
            for offset in range(i2-i1):
                # Insert ORIGINAL titles into map (using offset in CID list)
                con.execute('INSERT INTO choice_map VALUES (?,?)',
                            (lc_lut[iid[i1+offset]],
                             sc_lut[jid[j1+offset]]))
        elif tag == 'replace':
            if acceptAllReplacement and (ispan == jspan):
                print('\nAUTO create LVR--SOVC choice-map for: ({}) {}--{}'
                      .format(tag, iti[i1:i2], jti[j1:j2]))
                for offset in range(ispan):
                    con.execute('INSERT INTO choice_map VALUES (?,?)',
                                (lc_lut[iid[i1+offset]],
                                 sc_lut[jid[j1+offset]]))
            else:
                print('\nWARNING: '
                      'NOT creating LVR--SOVC choice-map for: {} {}({})--{}({})'
                      .format(tag,
                              iti[i1:i2],  ispan,
                              jti[j1:j2],  jspan))
                print('CONSIDER: Insert mappings for Choice(s)?')
                for offset in range(ispan):
                    print("  SQL: INSERT INTO choice_map VALUES ('{}','{}')"
                          .format(lc_lut[iid[i1+offset]],
                                  sc_lut[jid[j1+offset]]))
        else:
            print('\nWARNING: '
                  'NOT creating LVR--SOVC choice-map for: ({}) {}({})--{}({})'
                  .format(tag,
                          iti[i1:i2],  ispan,
                          jti[j1:j2],  jspan))
    print('\n\n###################################')
    print('Mapping can be added with sqlite. e.g.')
    print('  sqlite3 {} "INSERT INTO choice_map VALUES (\'LVRstr\',\'SOVCstr\')'
          .format(mapdb))
    print('  sqlite3 {} "INSERT INTO race_map VALUES (\'LVRstr\',\'SOVCstr\')'
          .format(mapdb))
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



