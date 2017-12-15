#! /usr/bin/env python
"""Command Line Interpreter for Operational use of vvote software.
"""


import sys
import argparse
import logging
import cmd


def my_func(arg1, arg2):
    """The work-horse function."""
    return(arg1, arg2)

class VvoteShell(cmd.Cmd):
    intro = 'Welcome to the vvote shell.   Type help or ? to list commands.\n'
    prompt = '(vvote) '
    file = None

    # ----- basic vvote commands -----
    def do_ingest(self, lvr_file, sovc_file):
        pass

##############################################################################

def main():
    "Parse command line arguments and do the work."
    print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='My shiny new python program',
        epilog='EXAMPLE: %(prog)s a b"'
        )
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('infile', type=argparse.FileType('r'),
                        help='Input file')
    parser.add_argument('outfile', type=argparse.FileType('w'),
                        help='Output output')

    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING')
    args = parser.parse_args()
    #!args.outfile.close()
    #!args.outfile = args.outfile.name

    #!print 'My args=',args
    #!print 'infile=',args.infile

    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    VvoteShell().cmdloop()

if __name__ == '__main__':
    main()
