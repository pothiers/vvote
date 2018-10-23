#! /usr/bin/env python
"""\
Store summary count of ballots from LVR.db back into LVR.db for convenience.

We store instead of emit because we will later compare to query against SOVC.db
Delimitter escapes need to be treated the same for both LVR and SOVC.

see also: lvr_db.py
"""


import sys
import argparse
import logging
import sqlite3
from pprint import pprint,pformat
#!from .mapping_db import MapDb
#!from . import sql
from vvote.mapping_db import MapDb
import vvote.sql as sql
    
def lvr_count_and_map(lvrdb, mapdb):
    """Count total votes in LVR (per choice), map to SOVC names."""
    mdb = MapDb(mapdb)
    mdb.load_lvr_sovc_luts()
    cur = sqlite3.connect(mapdb).cursor()
    raceMap = dict() # raceMap[lvrRaceId] => sovcRaceId
    for (conf,lrid,lti,srid,sti) in cur.execute(sql.race_map):
        raceMap[lrid] = srid
    choiceMap = dict() # choiceMap[lvrChoiceId] => sovcChoiceId
    for (conf,lrid,lcid,lti,scid,sti) in cur.execute(sql.choice_map):
        choiceMap[lcid] = scid

    con = sqlite3.connect(lvrdb)
    cur1 = con.cursor()
    cur2 = con.cursor()
    cur1.execute('DELETE FROM summary_totals;')
    for (rid,cid,ctitle,votes) in cur1.execute(sql.lvr_total_votes):
        if votes == 0: continue
        cur2.execute('INSERT INTO summary_totals VALUES (?,?,?)',
                     (mdb.sovc_rlut[raceMap[rid]],
                      mdb.sovc_clut[choiceMap[cid]],
                      votes))
    con.commit()
    con.close()
            


##############################################################################

def main():
    "Parse command line arguments and do the work."
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s "'
        )
    dfldb='LVR.db'
    dfmdb='MAP.db'
    dftot='lvr_totals.csv'
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('--lvrdb', '-l',
                        help='LVR sqlite DB')
    parser.add_argument('--mapdb', '-m', 
                        default=dfmdb,
                        help='MAP sqlite DB')
    parser.add_argument('--totals', '-t', 
                        default=dftot,
                        help='CSV of total votes in LVR (mapped to SOVC names)')

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
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    lvr_count_and_map(args.lvrdb, args.mapdb)
    print('Wrote LVR summary totals into: {}'.format(args.lvrdb))

if __name__ == '__main__':
    main()
