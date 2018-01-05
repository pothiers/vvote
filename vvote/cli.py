#! /usr/bin/env python
"""Command Line Interpreter for Operational use of vvote software.

Commands:
  - Convert Excel to CSV (LVR, SOVC)
  - Ingest LVR from CSV
  - Ingest SOVC from CSV
  - Create MAP (using LVR, SOVC)
  - Export MAPS (to allow editing; RACE, CHOICE)
  - Import MAPS (edited version; RACE, CHOICE)
  - Tally LVR; from LVR.db, store back in LVR.db, use SOVC Race,Choice names
  - Compare LVR talley to SOVC

Extra commands: (not needed for main flow)
  - Summarize LVR.db
  - Summarize SOVC.db
  - Summarize MAP.db

"""


import sys
import argparse
import logging
import cmd
import os
import os.path
from pathlib import PurePath
import sqlite3
import difflib


from .lvr_db import LvrDb
from .lvr_count import lvr_count_and_map
from .sovc_db import SovcDb
from .mapping_db import MapDb
from .xlsx2csv import xlsx2csv

def compare_totals(lvrdb, sovcdb, lvrtotals, sovctotals, diff):
    pass

class VvoteShell(cmd.Cmd):
    intro = '''\
Welcome to the vvote shell.   Type help or ? to list commands.
Type TAB after partial command for cmd completion.

EXAMPLES:
full_workflow ~/sandbox/vvote/tests/data/day1.lvr.csv ~/sandbox/vvote/tests/data/export1.sovc.csv
'''
    prompt = '(vvote) '
    file = None

    def __init__(self, echo=False, datadir='~/.vvote'):
        self.echo = echo
        self.datadir = PurePath(os.path.expanduser(datadir))
        self.lvrdb = str(self.datadir / 'LVR.db')
        self.sovcdb = str(self.datadir / 'SOVC.db')
        self.mapdb = str(self.datadir / 'MAP.db')
        self.racemap = str(self.datadir / 'RACEMAP.csv')
        self.choicemap = str(self.datadir / 'CHOICEMAP.csv')
        self.htmlfile = str(self.datadir / 'diff.html')
        self.textfile = str(self.datadir / 'diff.txt')
        
        os.makedirs(str(self.datadir), exist_ok=True)
        super(VvoteShell, self).__init__()
        
    def cmdloop_with_keyboard_interrupt(self):
        doQuit = False
        while doQuit != True:
            try:
                self.cmdloop()
                doQuit = True
            except KeyboardInterrupt:
                sys.stdout.write('\n')
            except Exception as err:
                print('ERROR in command: {}\n'.format(err))
                
    def precmd(self, line):
        if self.echo:
            print(line)
            return line
        else:
            return line

    ######################################################################
    ###     basic vvote commands
    ###

    def do_excel2csv(self, excel_csv):
        """excel2csv in_excel_file out_csv_file
        Convert Excel to CSV file."""
        excel_file,csv_file     = excel_csv.split()
        xlsx2csv(excel_file, csv_file)

    # lvrdb --database $out/LVR.db --incsv $out/day9.lvr.csv
    def do_ingest_lvr(self, lvr_csv):
        """ingest_lvr lvr_csv
        Ingest LVR CSV file into its own sqlite database."""
        db = LvrDb(self.lvrdb)
        csv = os.path.expanduser(lvr_csv)
        print('Ingesting CSV file ({}) into database ({})'
              .format(csv, self.lvrdb))
        db.insert_from_csv(csv)
        
    # sovcdb --database $out/SOVC.db --incsv $out/export9.sovc.csv 
    def do_ingest_sovc(self, sovc_csv):
        """ingest_sovc sovc_csv
        Ingest SOVC CSV file into its own sqlite database."""
        db = SovcDb(self.sovcdb)
        db.insert_from_csv(os.path.expanduser(sovc_csv))


    # makemapdb --new -l $out/LVR.db -s $out/SOVC.db --mapdb $out/MAP.db 
    # makemapdb -m $out/MAP.db --calc
    def do_create_map(self, arg):
        """create_map
        Create mapping from LVR to SOVC names (for Races and Choices)"""
        mdb = MapDb(self.mapdb, new=True)
        mdb.get_lvr_luts(self.lvrdb)
        mdb.get_sovc_luts(self.sovcdb)
        mdb.calc()


    # makemapdb -m $out/MAP.db --export
    def do_export_maps(self, arg):
        """export_maps
        Export Race and Choice maps for possible editing."""
        mdb = MapDb(self.mapdb, new=False)
        mdb.export(racemap_csv=self.racemap, choicemap_csv=self.choicemap)


    # makemapdb -m $out/MAP.db --import RACEMAP.csv CHOICEMAP.csv
    def do_import_maps(self, arg):
        """import_maps
        Import edited Race and Choice maps."""

        mdb = MapDb(self.mapdb, new=False)
        mdb.load_maps(self.racemap, self.choicemap)

    # lvrcnt --lvr $out/LVR.db --map $out/MAP.db
    def do_tally_lvr(self, arg):
        """tally_lvr
        Count votes in LVR database. Store back in database using SOVC names."""
        print('Inserting summary of votes into LVR db. (slow)')
        lvr_count_and_map(self.lvrdb, self.mapdb)

    def do_show_tally(self, arg):
        """show_tally
        Display previously computed tally ("tally_lvr") of LVR votes."""
        cur = sqlite3.connect(self.lvrdb).cursor()
        print('{}\t{}\t{}'.format('Race','Choice','Votes'))
        for (race,choice,votes) in cur.execute('SELECT * FROM summary_totals;'):
            print('{}\t{}\t{}'.format(race,choice,votes))


    # ~/sandbox/vvote/scripts/compare.sh
    def do_compare_totals(self, arg):
        """compare_totals 
        Compare total votes from LVR to SOVC."""
        sql_lvr = '''SELECT * FROM summary_totals ORDER BY race,choice;'''
        sql_sovc = '''SELECT 
  race.title as rt, 
  choice.title as ct,
  vote.count as votes
FROM vote, choice, race
WHERE 
  vote.choice_id = choice.choice_id 
  AND choice.race_id = race.race_id
  AND vote.precinct_code = \'ZZZ\'
GROUP BY rt, ct
ORDER BY rt, ct;'''

        cur = sqlite3.connect(self.lvrdb).cursor()
        cur.execute(sql_lvr)
        fromlines =  [str(tup) for tup in cur.fetchall()]
        
        cur2 = sqlite3.connect(self.sovcdb).cursor()
        cur2.execute(sql_sovc)
        tolines =  [str(tup) for tup in cur2.fetchall()]

        hd = difflib.HtmlDiff()
        html = hd.make_file(fromlines, tolines, fromdesc='LVR', todesc='SOVR')
        with open(self.htmlfile, mode='w') as f:
            print(html, file=f)
        print('Wrote full differences to HTML at: {}'.format(self.htmlfile))

        dif = difflib.Differ()
        with open(self.textfile, mode='w') as f:
            for line in dif.compare(fromlines,tolines):
                if line.startswith('  '): continue
                if line.startswith('? '): continue
                if line.endswith(', 0)'): continue
                print(line, file=f)
        print('Wrote delta differences to TEXT at: {}'.format(self.textfile))

            
    def do_full_workflow(self, lvr_sovc):
        """full_workflow lvr_excel sovc_excel
        Do all steps from CSV (LVR,SOVC) Input to Compare:
            ingest_lvr lvr_csv
            ingest_sovc sovc_csv
            create_map
            export_maps
            import_maps
            tally_lvr
            compare_totals diff.html"""
        # excel2csv lvr_excel lvr_csv
        # excel2csv sovc_excel sovc_csv

        lvr_csv, sovc_csv = lvr_sovc.split()
        dummy = ''
        print('Putting workflow intermediate results in: {}'
              .format(self.datadir))

        #!lvr_csv = str(self.datadir / 'LVR.csv')
        #!sovc_csv = str(self.datadir / 'SOVC.csv')
        #!print('Converting {} and {} to CSV'.format(lvr_excel, sovc_excel))
        #!self.do_excel2csv(lvr_excel + ' ' + lvr_csv)        
        #!self.do_excel2csv(sovc_excel  + ' ' + sovc_csv)        

        print('Ingest {} into LVR.db'.format(lvr_csv))
        self.do_ingest_lvr(lvr_csv)
        print('Ingest {} into SOVC.db'.format(sovc_csv))
        self.do_ingest_sovc(sovc_csv)

        self.do_create_map(dummy)
        self.do_export_maps(dummy)
        self.do_import_maps(dummy)

        print('Tally LVR votes into LVR.db')
        self.do_tally_lvr(dummy)
        self.do_compare_totals(dummy)

    def do_quit(self, arg):
        """quit (or EOF)
        Quit vvote Command Line Interpreter"""
        print('All done!')
        return True # abort
    do_EOF = do_quit
    
def start_cli(**kwargs):
    """The work-horse function."""
    #!VvoteShell(**kwargs).cmdloop()    
    VvoteShell(**kwargs).cmdloop_with_keyboard_interrupt()
    
##############################################################################
def main():
    "Parse command line arguments and do the work."
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    dfdir='~/.vvote/' #default output directory
    dflvrdb='LVR.db'
    dfsovcdb='SOVC.db'
    dfmapdb='MAP.db'
    parser.add_argument('-d', '--dir', 
                        default=dfdir,
                        help=('Directory to use for storing intermediate'
                              ' and final results.'
                              '  [default="{}"]').format(dfdir))
    parser.add_argument('-e', '--echo',
                        action='store_true',
                        help='Echo commands to stdout')
    parser.add_argument('--version', action='version', version='1.0.1')
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

    start_cli(echo=args.echo, datadir=args.dir)


if __name__ == '__main__':
    main()
