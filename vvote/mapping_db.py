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
    # Some of these are impossible for some Contests (no "write-in" for yes/no)
    fixed_mapping = [
        # LVR,        SOVC
        ('overvote', 'OVER VOTES'),
        ('undervote','UNDER VOTES'),
        ('Write-in', 'WRITE-IN')
        ]
    
    def __init__(self, mapdb, new=False):
        self.mapdb = mapdb
        self.con = sqlite3.connect(self.mapdb)
        # LVR db data
        self.lvr_rlut = dict() # lut[raceId] => raceTitle
        self.lvr_clut = dict() # lut[choiceId] => choiceTitle
        self.lvr_rclut = defaultdict(list) # lut[raceId] => [choiceId, ...]
        # SOVC db data
        self.sovc_rlut = dict() # lut[raceId] => raceTitle
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
        
        self.con.execute('DELETE from lvr_race;')
        for id,t in self.lvr_rlut.items():
            self.con.execute('INSERT INTO lvr_race VALUES (?,?)',(id, t))
        self.con.execute('DELETE from lvr_choice;')
        for id,t in self.lvr_clut.items():
            self.con.execute('INSERT INTO lvr_choice VALUES (?,?)',(id, t))

        self.con.commit()

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
              
    def load_lvr_sovc_luts(self):
        cur = self.con.cursor()
        cur.execute('SELECT lvr_filename,sovc_filename FROM source;')
        self.lvrdb,self.sovcdb = cur.fetchone()
        self.get_lvr_luts(self.lvrdb)
        self.get_sovc_luts(self.sovcdb)
        
    def calc(self):
        self.load_lvr_sovc_luts()
        self.con = sqlite3.connect(self.mapdb)
        
        self.con.execute('DELETE from race_map;')
        self.con.execute('DELETE from choice_map;')

        ### Compare Races of LVR,SOVC
        # ridmap:: [(conf, lvr_id, sovc_id,), ...]
        ridmap = self.gen_map_by_matchblocks(clean_races(self.lvr_rlut),
                                             self.sovc_rlut.items() )
        #! print('ridmap(conf,lvrid,sovcid)=',ridmap)
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
            #!self.print_lvr_race_choices(lvrRaceId)
            #!self.print_sovc_race_choices(sovcRaceId)
            lvr_lut = dict([(cid, self.lvr_clut[cid]) for cid in choiceIds])
            # use just generated ridmap to map LVR_RaceId to SOVC_RaceId
            sovc_lut = dict([(cid, self.sovc_clut[cid])
                             for cid in self.sovc_rclut[sovcRaceId]])
            # cidmap:: [(conf, lvr_id, sovc_id), ...]
            cidmap = self.gen_map_by_matchblocks(clean_choices(lvr_lut),
                                                 sovc_lut.items(),
                                                 lvr_raceid=lvrRaceId,
                                                 sovc_raceid=sovcRaceId )
            #print('DBG cidmap=',pformat(cidmap))
            self.insert_choice_map(cidmap,lvrRaceId, sovcRaceId)
            #!print('Choices map for race "{}":\n{}'
            #!      .format(self.lvr_rlut[lvrRaceId],
            #!               self.text_cidmap(cidmap)))

        self.con.commit()
        self.con.close()


    def insert_race_map(self,raceIdMap):
        for (conf, lvr_id, sovc_id) in raceIdMap:
            lvr_title = self.lvr_rlut.get(lvr_id, '<none>')
            sovc_title = self.sovc_rlut[sovc_id] if sovc_id else '<none>'
            self.con.execute('INSERT INTO race_map VALUES (?,?,?,?,?)',
                             (conf, lvr_id, lvr_title, sovc_id, sovc_title))

    def insert_choice_map(self,choiceIdMap, lvrRaceId, sovcRaceId):
        for (conf, lvr_id, sovc_id) in choiceIdMap:
            self.con.execute('INSERT INTO choice_map VALUES (?,?,?,?,?,?)',
                             (conf,
                              lvrRaceId, 
                              lvr_id,  self.lvr_clut.get(lvr_id, None),
                              sovc_id, self.sovc_clut.get(sovc_id, None)
                             ))


        
    def gen_map_by_matchblocks(self, cleaned_lvr_items, sovc_items,
                               lvr_raceid=None,
                               sovc_raceid=None ):
        """Generate LVR=>SOVC title mapping. 
For CHOICE map (if lvr_raceid provided), ignore fixed_mapping choices. They 
will be added later.
  lvr_items :: [(id,title), ...]
  RETURN:  idmap:: set([(conf, lvr_id, sovc_id), ...])"""
        idmap = set()
        #!print('DBG: init idmap=',pformat(idmap))
        fixed_lvr,fixed_sovc = zip(*self.fixed_mapping)
        lvr_items = [(id,title) for (id,title) in cleaned_lvr_items
                     if (title not in fixed_lvr)]
        sovc_items = [(id,title) for (id,title) in sovc_items
                      if (title not in fixed_sovc)]
        if len(lvr_items) == 0:
            return [(0,None,sid) for sid,stitle in sovc_items]
        iid,ititle = zip(*lvr_items)
        if len(sovc_items) == 0:
            return [(0,lid,None) for lid in iid]
        jid,jtitle = zip(*sovc_items)
        s = SequenceMatcher(None, ititle, jtitle)
        lvr_unmapped = set(iid)
        sovc_unmapped = set(jid)        
        for (lvr_idx, sovc_idx, size) in s.get_matching_blocks():
            for offset in range(size):
                lvr_id = iid[lvr_idx+offset]
                sovc_id = jid[sovc_idx+offset]
                lvr_unmapped.discard(lvr_id)
                sovc_unmapped.discard(sovc_id)
                idmap.add((1.0, lvr_id, sovc_id))
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
            idmap.add((bestconf, bestlvr, bestsovc))
        # If any LVR ids were not paired up, map them to NONE
        for lvr_id in lvr_unmapped:
            idmap.add((0, lvr_id, None))
        for sovc_id in sovc_unmapped:
            idmap.add((0, None, sovc_id))

        #### Add fixed_map for choices (WRITE-IN, etc.)
        if lvr_raceid != None:  
            # rcinv[choiceTitle] = choiceId
            lvr_rcinv = dict([(self.lvr_clut[cid],cid)
                              for cid in self.lvr_rclut[lvr_raceid]])
            sovc_rcinv = dict([(self.sovc_clut[cid],cid)
                              for cid in self.sovc_rclut[sovc_raceid]])
            for (lvr_title,sovc_title) in self.fixed_mapping:
                lvr_id = lvr_rcinv.get(lvr_title, None)
                sovc_id = sovc_rcinv.get(sovc_title, None)
                if lvr_id and sovc_id:
                    idmap.add((1, lvr_id, sovc_id))
        
        return idmap # set([(conf, lvr_id, sovc_id), ...])
        
    
    def export(self, racemap_csv='RACEMAP.csv', choicemap_csv='CHOICEMAP.csv' ):
        con = sqlite3.connect(self.mapdb)
        headers = 'Conf,LId,LTitle,SId,Stitle'.split(',')
        with open(racemap_csv, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, dialect='excel')
            writer.writerow(headers)
            for (conf, lid,lti,sid,sti) in con.execute(sql.race_map):
                writer.writerow([conf,lid,lti,sid,sti])

        #headers = 'Conf,LRace,LId,LTitle,SRace,SId,Stitle'.split(',')
        #ignoreTitles = ['WRITE-IN', 'OVER VOTES', 'UNDER VOTES']
        headers = 'Conf,LRaceId,LId,LTitle,SId,STitle'.split(',')
        with open(choicemap_csv, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile, dialect='excel')
            writer.writerow(headers)
            for (conf,lrti, lid,lti,sid,sti) in con.execute(sql.choice_map):
                #!if lti in ignoreTitles: continue
                #!if sti in ignoreTitles: continue
                writer.writerow([conf, lrti,lid,lti,sid,sti])
        print('Wrote racemap: {}, choicemap: {}'
              .format(racemap_csv, choicemap_csv))

    # VALIDATE:
    # 1. all text same as DB (not changed in CSV)
    # 2. still one-to-one mapping (LVR->SOVC)
    # 3. ChoiceId and Title still match for both LVR an SOVC
    # N. other??
    def validate_choice_row(self, row, orig, new):
        conf = float(row['Conf'])
        lraceid = int(row['LRaceId'])
        lid = None if row['LId'] == None else int(row['LId'])
        ltitle = row['LTitle']
        
        key = (lraceid, lid, ltitle)
        if not (0.0 <= conf  <= 1.0):
            raise Exception('Conf ({}) not in range [0.0:1.0]'.format(conf))
        if key in new:
            raise Exception('Duplicate LVR entry (LRaceId,LId,LTitle)={}'
                            .format((lraceid,lid, ltitle)))
        if key not in orig: 
            raise Exception('LVR entry (LRaceId,LId,LTitle) not in orig={}'
                            .format((lraceid,lid, ltitle)))
        if lraceid not in self.lvr_rlut:
            raise Exception('LRaceId ({}) not in LVR race list.'
                            .format(lraceid))

        if lid not in self.lvr_clut:
            raise Exception('LId ({}) not in LVR choices per DB.'
                            .format(lid))
        if self.lvr_clut[lid] != ltitle:
            raise Exception(('LId ({}) and LTitle ({}) do not correspond'
                             ' in DB ({}).')
                            .format(lid, ltitle, self.mapdb))
        if lid not in self.lvr_rclut[lraceid]:
            raise Exception('LId ({}) not in LVR choice list for race ({}).'
                            .format(lid,lraceid))

        if (row['SId'] != None) and (row['SId'] != ''):
            sid = int(row['SId'])
            stitle = row['STitle']
            if sid not in self.sovc_clut:
                raise Exception('SId ({}) not in SOVC choices per DB.'
                                .format(sid))
            if self.sovc_clut[sid] != stitle:
                raise Exception(('SId ({}) and STitle ({}) do not correspond'
                                 ' in DB ({}).')
                                .format(sid, stitle, self.mapdb))
        #!if sid not in self.sovc_rclut[lraceid]
        #!    raise Exception('SId ({}) not in SOVC choice list for race ({}).'
        #!                    .format(sid,lraceid))
        return True
        

    def load_choice_map(self, choicemap_csv='CHOICEMAP.csv'):
        self.load_lvr_sovc_luts()
        orig = dict() # orig[(raceId,lvrChoiceId,LvrChoiceTitl)=(conf, sid, sti)
        new  = dict() # new [(raceId,lvrChoiceId,LvrChoiceTitl)=(conf, sid, sti)
        for (conf,lrid, lid,lti,sid,sti) in self.con.execute(sql.choice_map):
            lidval = None if lid == None else int(lid)
            #orig[(int(lrid), lidval, lti)] = (float(conf), int(sid), sti)
            orig[(lrid, lidval, lti)] = (conf, sid, sti)
        errors = 0
        with open(choicemap_csv) as csvfile:
            for row in csv.DictReader(csvfile, dialect='excel'):
                if len(row['LId']) == 0: continue
                try:
                    self.validate_choice_row(row, orig, new)
                except Exception as err:
                    logging.error('Invalid CHOICE map row: {}; {}'
                                  .format(row,err))
                    errors += 1
                    continue
                else:
                    new[(row['LRaceId'],row['LId'],row['LTitle'])] = (
                        row['Conf'], row['SId'], row['STitle'])

        if errors == 0:
            self.con.execute('DELETE from choice_map;')
            for ((race,lid,ltitle), (conf,sid,stitle)) in new.items():
                self.con.execute('INSERT INTO choice_map VALUES(?,?,?,?,?,?)',
                                 (conf, race, lid, ltitle, sid, stitle))
            print('CHOICMAP imported from: {}'.format(choicemap_csv))
        else:
            logging.error('NOT importing CHOICEMAP due to {} errors.'
                          .format(errors))
                    
    def load_maps(self, racemap_csv, choicemap_csv):
        self.con = sqlite3.connect(self.mapdb)
        #self.load_race_map(racemap_csv=racemap_csv)
        print("WARNING: not importing RACEMAP!!!")
        self.load_choice_map(choicemap_csv=choicemap_csv)
        self.con.commit()


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
        ('YES/SÍ',   'YES'),
        ('YES/Sí',   'YES'),
        ('YES/SI',   'YES'),
    ]
    #! ('overvote', 'OVER VOTES'),
    #! ('undervote','UNDER VOTES'),
    #! ('Write-in', 'WRITE-IN'),

    for k in lut.keys():
        newlut[k] = rem_party(newlut[k])
        newlut[k] = newlut[k].translate(nukechars)
        for (a,b) in repstrs:
            newlut[k] = newlut[k].replace(a,b)
    return sorted(newlut.items(), key=lambda x: x[1])

    

def similar(lvr,sovc):
    "Symetric similarity [0,1].  1.0 for identical."
    if (lvr == None) or (sovc == None):
        return 0
    return SequenceMatcher(a=lvr, b=sovc).ratio()


          

##############################################################################

def main():
    "Parse command line arguments and do the work."
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
    parser.add_argument('--exportmaps', '-e', action='store_true',
                        help='Export mapping table suitable for editing')
    parser.add_argument('--importmaps', '-i', nargs=2,
                        help=('Import mapping tables from'
                              ' Races.csv and Choices.csv')  )
    
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
    if args.exportmaps:
        mdb.export()
    if args.importmaps:
        mdb.load_maps(*args.importmaps)
        
if __name__ == '__main__':
    main()



