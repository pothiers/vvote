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
from itertools import product

from difflib import SequenceMatcher
from pprint import pprint,pformat
import copy
import csv
from collections import defaultdict

from . import sql

##############################################################################
### Database
###
class MapDb():
    """Manage Map database (sqlite3 format).  It provides tables to map 
Race and Choice titles from LVR strings to SOVC strings."""
    def __init__(self, mapdb, new=False):
        self.mapdb = mapdb
        self.con = sqlite3.connect(self.mapdb)
        # LVR db data
        self.lvr_rlut = dict() # lut[raceId] => raceTitle
        self.lvr_clut = dict() # lut[choiceId] => choiceTitle
        self.lvr_rclut = defaultdict(list) # lut[raceId] => [choiceId, ...]
        # SOVC db data
        self.sovc_rlut = dict() # lut[raceIdd] => raceTitle
        self.sovc_clut = dict() # lut[choiceId] => choiceTitle
        self.sovc_rclut = defaultdict(list) # lut[raceId] => [choiceId, ...]
        if new:
            print('Creating new map db: {}'.format(mapdb))
            if os.path.exists(mapdb):
                os.remove(mapdb)
                print('Removed existing MAP database: {}'.format(mapdb))
                self.con = sqlite3.connect(mapdb)
            self.con.executescript(sql.map_schema)
            self.con.execute('INSERT INTO source VALUES(?,?,?,?)',
                             (1,mapdb,None,None))
            self.con.commit()
            self.con.close()

    def get_lvr_luts(self, lvrdb):
        """Extract 3 LUTS from DB that contain choices per race and 
    map choice and race ids to corresponding titles."""
        self.con = sqlite3.connect(self.mapdb)
        self.con.execute("UPDATE source SET lvr_filename = ? WHERE sid=1",
                         (lvrdb,))
        con = sqlite3.connect(lvrdb)
        for (rid,rti,cid,cti) in con.execute(sql.lvr_choices):
            self.lvr_rlut[rid] = rti
            self.lvr_clut[cid] = cti
            self.lvr_rclut[rid].append(cid)
        self.con.commit()
        self.con.close()

    def get_sovc_luts(self, sovcdb):
        """Extract 3 LUTS from DB that contain choices per race and 
    map choice and race ids to corresponding titles."""
        self.con = sqlite3.connect(self.mapdb)
        self.con.execute("UPDATE source SET sovc_filename = ? WHERE sid=1",
                         (sovcdb,))
        con = sqlite3.connect(sovcdb)
        for (rid,rti,cid,cti) in con.execute(sql.sovc_choices):
            self.sovc_rlut[rid] = rti
            self.sovc_clut[cid] = cti
            self.sovc_rclut[rid].append(cid)
        self.con.commit()
        self.con.close()
    
    def text_cidmap(self, cidmap):
        """idmap:: [(conf, lvr_id, sovc_id,), ...]"""
        return pformat([(conf, self.lvr_clut.get(lid), self.sovc_clut.get(sid))
                        for (conf,lid,sid) in cidmap])

    def print_lvr_race_choices(self, raceId):
        print('LVR Choices for race: {}\n{}'
              .format(self.lvr_rlut[raceId],
                      [self.lvr_clut[choice_id]
                       for choice_id in self.lvr_rclut[raceId]]))

    def print_sovc_race_choices(self, raceId):
        print('SOVC Choices for race: {}\n{}'
              .format(self.sovc_rlut[raceId],
                      [self.sovc_clut[choice_id]
                       for choice_id in self.sovc_rclut[raceId]]))
              
    
    def calc(self):
        cur = self.con.cursor()
        cur.execute('SELECT lvr_filename,sovc_filename FROM source;')
        self.lvrdb,self.sovcdb = cur.fetchone()
        self.get_lvr_luts(self.lvrdb)
        self.get_sovc_luts(self.sovcdb)
        self.con = sqlite3.connect(self.mapdb)
        
        self.con.execute('DELETE from race_map;')
        self.con.execute('DELETE from choice_map;')

        ### Compare Races of LVR,SOVC
        # ridmap:: [(conf, lvr_id, sovc_id,), ...]

        #!ridmap = self.gen_map_by_opcodes(clean_races(self.lvr_rlut),
        #!                                 self.sovc_rlut.items())
        ridmap = self.gen_map_by_matchblocks(clean_races(self.lvr_rlut),
                                             self.sovc_rlut.items())
        print('ridmap(conf,lvrid,sovcid)=',ridmap)
        lvrmaplist = [lvrid for (c,lvrid,sovcid) in ridmap]
        ridmapLut = dict([(lvrid,sovcid) for (c,lvrid,sovcid) in ridmap])
        self.insert_race_map(ridmap)

        ### Compare Choices of LVR,SOVC (choices for each race independent)
        missing = 0
        for lvrRaceId,choiceIds in self.lvr_rclut.items():
            if lvrRaceId not in lvrmaplist:
                logging.warning('There is no mapping of LVR race "{}" to SOVC'
                                .format(self.lvr_rlut[lvrRaceId]))
                missing += 1
                continue
            sovcRaceId = ridmapLut[lvrRaceId]
            self.print_lvr_race_choices(lvrRaceId)
            self.print_sovc_race_choices(sovcRaceId)
            lvr_lut = dict([(cid, self.lvr_clut[cid]) for cid in choiceIds])
            # use just generated ridmap to map LVR_RaceId to SOVC_RaceId
            sovc_lut = dict([(cid, self.sovc_clut[cid])
                             for cid in self.sovc_rclut[sovcRaceId]])
            print('len(lvr_lut)=',len(lvr_lut))
            print('len(sovc_lut)=',len(sovc_lut))
            #!cidmap = self.gen_map_by_opcodes(clean_choices(lvr_lut),
            #!                                 sovc_lut.items())
            cidmap = self.gen_map_by_matchblocks(clean_choices(lvr_lut),
                                                 sovc_lut.items())
            self.insert_choice_map(cidmap,lvrRaceId, sovcRaceId)
            print('Choices map for race "{}":\n{}'
                  .format(self.lvr_rlut[lvrRaceId],
                           self.text_cidmap(cidmap)))

        print('Missing {} LVR races'.format(missing))
        self.con.commit()
        self.con.close()


    def insert_race_map(self,raceIdMap):
        for (conf, lvr_id, sovc_id) in raceIdMap:
            lvr_title = self.lvr_rlut[lvr_id] if lvr_id else '<none>'
            sovc_title = self.sovc_rlut[sovc_id] if sovc_id else '<none>'
            self.con.execute('INSERT INTO race_map VALUES (?,?,?,?,?)',
                             (conf, lvr_id, lvr_title, sovc_id, sovc_title))

    def insert_choice_map(self,choiceIdMap, lvrRaceId, sovcRaceId):
        #!print('insert_choice_map: lvrRace="{}", sovcRace="{}", choicemap={}'
        #!      .format(self.lvr_rlut.get(lvrRaceId,None),
        #!              self.sovc_rlut.get(sovcRaceId,None),
        #!              [(self.lvr_clut[lid],self.sovc_clut.get(sid,None))
        #!                for (conf,lid,sid) in choiceIdMap]))
        for (conf, lvr_id, sovc_id) in choiceIdMap:
            self.con.execute('INSERT INTO choice_map VALUES (?,?,?,?,?)',
                             (conf,
                              lvr_id,  self.lvr_clut[lvr_id],
                              sovc_id, self.sovc_clut.get(sovc_id, None)
                             ))

        
    def gen_map_by_matchblocks(self, cleaned_lvr_items, sovc_items):
        """RETURN  idmap:: [(conf, lvr_id, sovc_id,), ...]"""
        idmap = list() 
        #!print('cleaned_lvr_items=',cleaned_lvr_items)
        #!print('sovc_items=',sovc_items)
        iid,ititle = zip(*cleaned_lvr_items)
        if len(sovc_items) == 0:
            return [(0,lid,None) for lid in iid]

        jid,jtitle = zip(*sovc_items)
        s = SequenceMatcher(None, ititle, jtitle)
        #!print('SM.matching_blocks: \n{}'
        #!      .format(pformat(s.get_matching_blocks())))
        lvr_unmapped = set(iid)
        sovc_unmapped = set(jid)        
        #!print('DBG-0: Num unmappedLVR={}, unmappedSOVC={}'
        #!      .format(len(lvr_unmapped), len(sovc_unmapped)))
        for (lvr_idx, sovc_idx, size) in s.get_matching_blocks():
            for offset in range(size):
                lvr_id = iid[lvr_idx+offset]
                sovc_id = jid[sovc_idx+offset]
                lvr_unmapped.discard(lvr_id)
                sovc_unmapped.discard(sovc_id)
                idmap.append((1.0, lvr_id, sovc_id))
        #!print('DBG-1: idmap=',idmap)
        #!print('DBG-1: Num unmappedLVR={}, unmappedSOVC={}'
        #!      .format(len(lvr_unmapped), len(sovc_unmapped)))

        lvr_lut = dict(cleaned_lvr_items)
        sovc_lut = dict(sovc_items)
        bestlvr = None
        bestsovc = None
        while (len(lvr_unmapped) != 0) and (len(sovc_unmapped) != 0):
            bestconf = -1
            for lvr_id,sovc_id in product(lvr_unmapped,sovc_unmapped):
                conf = similar(lvr_lut[lvr_id], sovc_lut[sovc_id])
                if conf > bestconf:
                    bestconf = conf
                    bestlvr = lvr_id
                    bestsovc = sovc_id
            lvr_unmapped.discard(bestlvr)
            sovc_unmapped.discard(bestsovc)
            idmap.append((bestconf, bestlvr, bestsovc))
        # If any LVR ids were not paired up, map them to NONE
        for lvr_id in lvr_unmapped:
            idmap.append((0, lvr_id, None))
        #!print('DBG-2: idmap=\n',pformat(idmap))
        #!print('DBG-2: Num unmappedLVR={}, unmappedSOVC={}'
        #!      .format(len(lvr_unmapped), len(sovc_unmapped)))
        return idmap
        
    def OBSOLETE_gen_map_by_opcodes(self, lvr_items, sovc_items):
        """RETURN  idmap:: [(conf, lvr_id, sovc_id), ...]"""
        idmap = list() 
        #!print('lvr_items=',lvr_items)
        #!print('sovc_items=',sovc_items)
        iid,ititle = zip(*lvr_items)
        jid,jtitle = zip(*sovc_items)
        s = SequenceMatcher(None, ititle, jtitle)
        print('GEN_MAP_BY_OPCODES:')
        print('LVR titles:\n{}'.format(pformat(ititle)))
        print('SOVC title:\n{}'.format(pformat(jtitle)))
        print('SM.matching_blocks: \n{}'
              .format(pformat(s.get_matching_blocks())))
        print('SM.opcodes: \n{}'.format(pformat(s.get_opcodes())))

        # Possible tags: equal, delete, insert, replace
        # Insert ORIGINAL titles into map (using offset in title list)
        for (tag, i1, i2, j1, j2) in s.get_opcodes():
            ispan = i2-i1
            jspan = j2-j1
            if tag == 'equal':
                # a[i1:i2] == b[j1:j2] (the sub-sequences are equal).
                for offset in range(ispan):
                    conf=similar(ititle[i1+offset], jtitle[j1+offset])
                    idmap.append((conf, iid[i1+offset], jid[j1+offset]))
            elif tag == 'replace':
                # [i1:i2] should be replaced by b[j1:j2].
                if (ispan == jspan):
                    for offset in range(ispan):
                        conf=similar(ititle[i1+offset], jtitle[j1+offset])
                        idmap.append((conf, iid[i1+offset], jid[j1+offset]))
                else:
                    # There are diff numbers of titles in LVR and SOVC.
                    # Insert each separately.
                    for offset in range(ispan):
                        idmap.append((0, iid[i1+offset], None))
                    for offset in range(jspan):
                        idmap.append((0, None, jid[j1+offset]))
            elif tag == 'delete':    # No SOVC, add to LVR
                # a[i1:i2] should be deleted. Note that j1 == j2 in this case.
                for offset in range(ispan):
                    conf=similar(ititle[i1+offset], jtitle[j1+offset])
                    idmap.append((0, iid[i1+offset], None))
            elif tag == 'insert':    # No LVR, add to SOVC
                # b[j1:j2] should be inserted at a[i1:i1]. NB i1 == i2 this case.
                for offset in range(jspan):
                    conf=similar(ititle[i1+offset], jtitle[j1+offset])
                    idmap.append((0, None, jid[j1+offset]))

        return idmap
    
    def export(self, racemap_csv='RACEMAP.csv', choicemap_csv='CHOICEMAP.csv' ):
        con = sqlite3.connect(self.mapdb)
        headers = 'Conf,LId,LTitle,SId,Stitle'.split(',')
        with open(racemap_csv, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, dialect='excel')
            writer.writerow(headers)
            for (conf,lid,lti,sid,sti) in con.execute(sql.race_map):
                writer.writerow([conf,lid,lti,sid,sti])

        #headers = 'Conf,LRace,LId,LTitle,SRace,SId,Stitle'.split(',')
        headers = 'Conf,LId,LTitle,SId,Stitle'.split(',')
        with open(choicemap_csv, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, dialect='excel')
            writer.writerow(headers)
            for (conf,lid,lti,sid,sti) in con.execute(sql.choice_map):
                writer.writerow([conf, lid,lti,sid,sti])
        print('Wrote racemap: {}, choicemap: {}'
              .format(racemap_csv, choicemap_csv))



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


# Normalize differentces between LVR and SOVC choices
# LVR may contain unicode
def clean_races(lut):
    """Normalize dict of races.  
lut[raceId] => newRaceTitle
RETURN: [(raceId,newRaceTitle), ...];  Sorted by TITLE.
"""
    newlut = copy.copy(lut) # newlut[cid] => title
    #
    # (no change)
    #
    return sorted(newlut.items(), key=lambda x: x[1])    

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
lut[choiceId] => newChoiceTitle
RETURN: [(choiceId,newChoiceTitle), ...];  Sorted by TITLE.
"""
    newlut = copy.copy(lut) # newlut[cid] => title
    # remove chars: parens, double-quotes
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

    
def insert_choice_by_opcodes(con, llut, lvr_lut, slut, sovc_lut):
    def insert_choice_titles(ispan, i1, i2, j1, j2):
        sql='INSERT INTO choice_map VALUES (?,?,?,?,?,?,?)'



#!def insert_race_by_opcodes(con, llut, lvr_lut, slut, sovc_lut):
#!    """ Insert RACE map
#!llut:: llut[id] => lvr_title
#!lvr_lut:: lut[raceId] => [choiceId, ...]
#!slut:: slut[id] => sovc_title
#!sovc_lut:: lut[raceId] => [choiceId, ...]
#!"""
#!    def insert_race_titles(ispan, i1, i2, j1, j2):
#!        sql='INSERT INTO race_map VALUES (?,?,?,?,?)'
#!        for offset in range(ispan):
#!            conf=similar(iti[i1+offset], jti[j1+offset])
#!            con.execute(sql, (conf,
#!                              iid[i1+offset], llut[iid[i1+offset]],
#!                              iid[i1+offset], slut[jid[j1+offset]]))
#!    con.execute('DELETE from race_map;')
#!
#!
#!    iid,iti = zip(*lvr_lut)
#!    jid,jti = zip(*sovc_lut)
#!    s = SequenceMatcher(None, iti, jti)
#!    print('INSERT for: RACE_MAP')
#!    print('LVR titles:\n{}'.format(pformat(iti)))
#!    print('SOVC title:\n{}'.format(pformat(jti)))
#!    print('SM.matching_blocks: \n{}'.format(pformat(s.get_matching_blocks())))
#!    print('SM.opcodes: \n{}'.format(pformat(s.get_opcodes())))
#!    
#!    # Possible tags: equal, delete, insert, replace
#!    # Insert ORIGINAL titles into map (using offset in title list)
#!    for (tag, i1, i2, j1, j2) in s.get_opcodes():
#!        ispan = i2-i1
#!        jspan = j2-j1
#!        if tag == 'equal':
#!            # a[i1:i2] == b[j1:j2] (the sub-sequences are equal).
#!            for offset in range(ispan):
#!                conf=similar(iti[i1+offset], jti[j1+offset])
#!                con.execute(sql, (conf,
#!                                  iid[i1+offset], llut[iid[i1+offset]],
#!                                  iid[i1+offset], slut[jid[j1+offset]]))
#!        elif tag == 'replace':
#!            # [i1:i2] should be replaced by b[j1:j2].
#!            if (ispan == jspan):
#!                for offset in range(ispan):
#!                    conf=similar(iti[i1+offset], jti[j1+offset])
#!                    con.execute(sql, (conf,
#!                                      iid[i1+offset], llut[iid[i1+offset]],
#!                                      jid[j1+offset], slut[jid[j1+offset]]))
#!            else:
#!                # There are diff numbers of titles in LVR and SOVC.
#!                # Insert each separately.
#!                for offset in range(ispan):
#!                    con.execute(sql, (0,
#!                                      iid[i1+offset], llut[iid[i1+offset]],
#!                                      -1, ''))
#!                for offset in range(jspan):
#!                    con.execute(sql, (0,
#!                                      -1, '',
#!                                      jid[j1+offset], slut[jid[j1+offset]]))
#!        elif tag == 'delete':    # No SOVC, add to LVR
#!            # a[i1:i2] should be deleted. Note that j1 == j2 in this case.
#!            for offset in range(ispan):
#!                con.execute(sql, (0,
#!                                  iid[i1+offset], llut[iid[i1+offset]],
#!                                  -1, ''))
#!        elif tag == 'insert':    # No LVR, add to SOVC
#!            # b[j1:j2] should be inserted at a[i1:i1]. NB i1 == i2 in this case.
#!            for offset in range(jspan):
#!                con.execute(sql, (0,
#!                                  -1, '',
#!                                  jid[j1+offset], slut[jid[j1+offset]]))


def similar(lvr,sovc):
    "Symetric similarity [0,1].  1.0 for identical."
    if (lvr == None) or (sovc == None):
        return 0
    return SequenceMatcher(a=lvr, b=sovc).ratio()


          
#!def import(mapdb, racemap_csv='RACEMAP.csv', choicemap_csv='CHOICEMAP.csv' ):
#!    """Read RACEMAP and CHOICEMAP as CSV and store in mapdb.
#!VERIFY:
#!1. no change was made to any text
#!2. there is still a one-to-one mapping
#!"""
#!    pass

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

    parser.add_argument('--new', '-n', action='store_true',
                        help='Create NEW map DB')
    parser.add_argument('--calc', '-c', action='store_true',
                        help='Calculating mapping (and store in db)')
    parser.add_argument('--pretty', '-p', action='store_true',
                        help='Pretty-print mapping')
    parser.add_argument('--export', '-e', action='store_true',
                        help='Export mapping suitable for editing')
    
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


    mdb = MapDb(args.mapdb, new=args.new)
    
    #!if args.lvrdb and args.sovcdb:
    #!    print('Overwriting map data in "{}" from contents of "{}", "{}"'
    #!          .format(args.mapdb, args.lvrdb, args.sovcdb))
    #!    gen_mapping(args.lvrdb, args.sovcdb, args.mapdb)
    if args.lvrdb:
        mdb.get_lvr_luts(args.lvrdb)
    if args.sovcdb:
        mdb.get_sovc_luts(args.sovcdb)

    if args.calc:
        print('(re)Calculating mapping from map data')
        mdb.calc()
#!    if args.pretty:
#!        print('Printing current mapping')
#!        printmap()
    if args.export:
        mdb.export()
        
if __name__ == '__main__':
    main()



