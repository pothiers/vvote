# Create sample data from full data set using:
#   vvote/scripts/gen_csv_sample.sh
#
# EXAMPLE:
#   cd ~/sandbox/vvote/vvote
#   python -m unittest tests/test_counts.py
#

import unittest
import warnings
import logging
import sys
import os.path
from pathlib import PurePath
from contextlib import contextmanager

from vvote.lvr_db import LvrDb

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


class TestVvote(unittest.TestCase):
    maxDiff = None # too see full values in DIFF on assert failure

    def setUp(self):
        self.datadir = PurePath(os.path.expanduser('~/.test-vvote'))
        self.lvrdb = str(self.datadir / 'LVR.db')
        self.sovcdb = str(self.datadir / 'SOVC.db')
        self.mapdb = str(self.datadir / 'MAP.db')
        self.racemap = str(self.datadir / 'RACEMAP.csv')
        self.choicemap = str(self.datadir / 'CHOICEMAP.csv')

    
    #@testcase_log_console(logger)
    def test_lvr_0(self):
        
        db = LvrDb(self.lvrdb)
        db.insert_from_csv(lvr_csv)
        self.assertEqual(2,0)
