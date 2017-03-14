#! /usr/bin/env python3
"""Transpose excel file
"""

import sys
import argparse
import logging

from . import excel_utils as eu

##############################################################################

def main():
    "Parse command line arguments and do the work."
    #print('EXECUTING: %s\n\n' % (' '.join(sys.argv)))
    parser = argparse.ArgumentParser(
        description='Transpose rows/columns from one Excel file to another',
        epilog='EXAMPLE: %(prog)s in.xlsx transposed.xlsx'
        )
    parser.add_argument('--version', action='version', version='1.0.1')
    parser.add_argument('infile', type=argparse.FileType('r'),
                        help='Input XSLX file')
    parser.add_argument('outfile', type=argparse.FileType('w'),
                        help='Transposed XSLX file')

    parser.add_argument('-f', '--format',
                        help='Format of output file',
                        choices=['text', 'SOVC'],
                        default='text')
    parser.add_argument('--loglevel',
                        help='Kind of diagnostic output',
                        choices=['CRTICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG'],
                        default='WARNING')
    args = parser.parse_args()
    args.infile.close()
    args.infile = args.infile.name
    args.outfile.close()
    args.outfile = args.outfile.name

    log_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(log_level, int):
        parser.error('Invalid log level: %s' % args.loglevel)
    logging.basicConfig(level=log_level,
                        format='%(levelname)s %(message)s',
                        datefmt='%m-%d %H:%M')
    logging.debug('Debug output is enabled in %s !!!', sys.argv[0])

    eu.transpose(args.intfile, args.outfile)
    
if __name__ == '__main__':
    main()
