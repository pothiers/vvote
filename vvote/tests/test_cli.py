# EXAMPLE:
#   cd ~/sandbox/vvote/vvote
#   python -m unittest tests.test_cli.TestCli.test_ingest_lvr
#   python -m unittest tests/test_cli.py
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

    def setUp(self):
        self.datadir = PurePath(os.path.expanduser('~/.vvote-test-out'))
        self.lvrdb = str(self.datadir / 'LVR.db')
        self.sovcdb = str(self.datadir / 'SOVC.db')
        self.mapdb = str(self.datadir / 'MAP.db')
        self.racemap = str(self.datadir / 'RACEMAP.csv')
        self.choicemap = str(self.datadir / 'CHOICEMAP.csv')
        self.htmlfile = str(self.datadir / 'diff.html')
        self.textfile = str(self.datadir / 'diff.txt')
        os.makedirs(str(self.datadir), exist_ok=True)


    #@testcase_log_console(logger)
    def test_ingest_lvr(self):
        vcli=cli.VvoteShell(datadir=self.datadir)
        vcli.onecmd('ingest_lvr ~/sandbox/vvote/tests/data/day1.lvr.csv')
        self.assertTrue(os.path.exists(self.lvrdb))
