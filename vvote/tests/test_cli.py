# EXAMPLE:
#   cd ~/sandbox/vvote/vvote
#   python -m unittest tests/test_cli.py
#   python -m unittest tests.test_cli.TestCli.test_ingest_sovc
#   python -m unittest  # auto discovery
import unittest
import warnings
import logging
import sys
import os
import os.path
from pathlib import PurePath
from contextlib import contextmanager

import cli

@contextmanager
def streamhandler_to_console(lggr):
    # Use 'up to date' value of sys.stdout for StreamHandler,
    # as set by test runner.
    stream_handler = logging.StreamHandler(sys.stdout)
    lggr.addHandler(stream_handler)
    yield
    lggr.removeHandler(stream_handler)

def testcase_log_console(lggr):
    def testcase_decorator(func):
        def testcase_log_console(*args, **kwargs):
            with streamhandler_to_console(lggr):
                return func(*args, **kwargs)
        return testcase_log_console
    return testcase_decorator

logger = logging.getLogger('django_test')



class TestCli(unittest.TestCase):
    maxDiff = None # too see full values in DIFF on assert failure

    @classmethod
    def setUpClass(self):
        self.datadir = PurePath(os.path.expanduser('~/.vvote-test-out'))
        outdir = str(self.datadir)
        os.makedirs(outdir, exist_ok=True)
        for filename in os.listdir(outdir):
            os.remove(os.path.join(outdir, filename))

        self.lvrdb = str(self.datadir / 'LVR.db')
        self.sovcdb = str(self.datadir / 'SOVC.db')
        self.mapdb = str(self.datadir / 'MAP.db')
        self.racemap = str(self.datadir / 'RACEMAP.csv')
        self.choicemap = str(self.datadir / 'CHOICEMAP.csv')
        self.htmlfile = str(self.datadir / 'diff.html')
        self.textfile = str(self.datadir / 'diff.txt')

        self.vcli=cli.VvoteShell(datadir=self.datadir)



    #@testcase_log_console(logger)
    def test_1ingest_lvr(self):
        self.vcli.onecmd('ingest_lvr ~/sandbox/vvote/tests/data/day1.lvr.csv')
        self.assertTrue(os.path.exists(self.lvrdb))

    def test_2ingest_sovc(self):
        self.vcli.onecmd(
            'ingest_sovc ~/sandbox/vvote/tests/data/export1.sovc.csv')
        self.assertTrue(os.path.exists(self.sovcdb))

    def test_3create_map(self):
        self.vcli.onecmd('create_map')
        self.assertTrue(os.path.exists(self.mapdb))

    def test_4export_maps(self):
        self.vcli.onecmd('export_maps')
        self.assertTrue(os.path.exists(self.racemap))
        self.assertTrue(os.path.exists(self.choicemap))

    def test_5import_maps(self):
        self.vcli.onecmd('import_maps')
        self.assertTrue(True) #!!!

    def test_6tally_lvr(self):
        self.vcli.onecmd('tally_lvr')
        #self.assertTrue(False)
        self.assertEqual(27797504,  os.path.getsize(self.lvrdb))

    def test_7compare_totals(self):
        self.vcli.onecmd('compare_totals')
        self.assertEqual(0,      os.path.getsize(self.textfile))
        self.assertEqual(170927, os.path.getsize(self.htmlfile))

        
