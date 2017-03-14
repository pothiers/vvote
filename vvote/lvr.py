#! /usr/bin/env python3
"""Extract from List of Vote Records (LVR)
"""

import copy
from collections import defaultdict
from openpyxl import load_workbook

class Lvr():
    """Maintain List of Vote Records (LVR). Its an excel (.xslx) file
that represents contents from a set of ballots.

   Row 1:: Race titles (None over columns representing choices beyond first)
   Row 2 to N:: Choices

   Col 4 to M::
"""
    MARKER='Cast Vote Record'
    nontitles = set(['Cast Vote Record',
                     'Serial Number',
                     'Precinct',
                     'Ballot Style'])

    def __init__(self, lvr_file, # Excel (.xslx) filename,
                 verbose=False):
        wb = load_workbook(filename=lvr_file, read_only=True)
        ws = wb.active
        if (ws.max_row == 1) or (ws.max_column == 1):
            ws.max_row = ws.max_column = None
            ws.calculate_dimension(force=True)
        totalsrow = ws.max_row - 1        
        if verbose:
            print('DBG: file={}, ws.max_row = {}, ws.max_column = {}'
                  .format(lvr_file, ws.max_row, ws.max_column))

        if ws.cell(row=1, column=1).value.strip() != self.MARKER:
            msg = ('Row={}, Col={} is "{}" but expected "{}"'
                   .format(totalsrow, 1,
                           ws.cell(row=1, column=1).value,
                           self.MARKER ))
            raise 'Invalid LVR ({}); {}'.format(lvr_file, msg)

        self.filename = lvr_file
        self.ws = ws
        self.max_row = ws.max_row
        self.max_column = ws.max_column


    def count_votes(self,
                    verbose=False,
                    nrows = 10000, # progress every N rows iff verbose==True
                    na_tag='<OOD>', # Out of District Ballots
                    writeintag='Write-in',
                    overvotetag='overvote',
                    undervotetag='undervote'):
        choices = defaultdict(set) # choices[race] = set([choice1, choice2,...])
        orderedchoices = dict() # d[race] => [choice1, ...]
        raceballot = list() # single ballot for single race, list(choice1, ...])
        votes = defaultdict(lambda : defaultdict(int)) # votes[race][choice] = cnt
        n_votes = defaultdict(int)  # n_votes[race] => num-to-vote-for

        coltitle = dict() # coltitle[column] => racetitle
        orderedraces = list()
        prevtitle = None
        ridx = 0
        ws = self.ws
        for row in ws.rows:
            ridx += 1
            cidx = 0
            if verbose:
                if (ridx % nrows) == 0:
                    print('# processed {} ballots'.format(ridx))
            for cell in row:
                cidx += 1
                #print('# DBG-0: ridx={} cidx{}'.format(ridx,cidx))

                # Ignore the (leading) columns that are not Race Titles
                if ridx == 1 and cell.value in self.nontitles:
                    continue

                if ridx == 1: # header
                    if cell.value != None:
                        race = cell.value.strip()
                        orderedraces.append(race)
                        n_votes[race] = 1
                        #!choices[race].add(overvotetag)
                        #!choices[race].add(writeintag)
                        #!choices[race].add(na_tag)
                    else: # vote-for-N race
                        n_votes[race] += 1
                    coltitle[cidx] = race
                else: # ballots
                    if cidx not in coltitle:
                        # Skip columns we don't care about
                        continue

                    if (cell.value == '' or cell.value == None):
                        choice = na_tag
                    else:
                        #choice = clean_choice(cell.value)
                        choice = cell.value
                    race = coltitle[cidx]
                    next_race = coltitle[cidx+1] if cidx < ws.max_column else None
                    #print('# DBG-0: race="{}"'.format(race))
                    raceballot.append(choice)
                    if race != next_race: # finished one race, one ballot
                        #print('DBG-1: raceballot={}'.format(raceballot))
                        if undervotetag in raceballot:
                            undervote_m = ('undervote-{}'
                                           .format(raceballot.count(undervotetag)))
                            votes[race][undervote_m] += 1
                            #!choices[race].add(undervote_m)
                            raceballot.append(undervote_m)
                        if overvotetag in raceballot:
                            assert raceballot.count(overvotetag) == n_votes[race]
                            votes[race][overvotetag] += 1
                        if na_tag in raceballot:
                            assert raceballot.count(na_tag) == n_votes[race]
                            votes[race][na_tag] += 1
                        for c in raceballot:
                            if c == writeintag:
                                #!choices[race].add(c)
                                votes[race][c] += 1                            
                        raceballot = [c for c in raceballot
                                      if ((c != undervotetag)
                                          and (c != overvotetag)
                                          and (c != na_tag)
                                          and (c != writeintag)
                                      )]
                        # no dupes
                        assert len(raceballot) == len(set(raceballot)), 'Duplicates in: {}'.format(raceballot)

                        for choice in set(raceballot):
                            choices[race].add(choice)
                            votes[race][choice] += 1
                        orderedchoices[race] = copy.copy(raceballot)
                        raceballot = list() # single ballot for single race

        nballots = ridx-1
        print('Processed {} ballots'.format(nballots))
        return votes, choices, n_votes, nballots, orderedraces, orderedchoices

        
    def get_titles(self,
                   nrows = 10000, # progress every N rows iff verbose==True
                   verbose=False):
        "RETURN: dict[(race,choice)] => count"

        ws = self.ws
        other = ['undervote', 'Write-in']
        races = set()
        choices = set()
        ignorecolumns = set()
        ridx = 0
        for row in ws.rows:
            ridx += 1
            cidx = 0
            if verbose:
                if (ridx % nrows) == 0:
                    print('# processed {} ballots'.format(ridx))
            for cell in row:
                cidx += 1
                if cidx in ignorecolumns:
                    continue
                # Ignore the (leading) columns that are not Race Titles
                if ridx == 1 and cell.value in self.nontitles:
                    ignorecolumns.add(cidx)
                    continue
                if ridx == 1: # header
                    if cell.value != None:
                        races.add(cell.value.strip())
                else: #ballots
                    if (cell.value == '' or cell.value == None or cell.value.strip() == ''):
                        continue
                    choices.add(cell.value.strip())
        return races, (choices - set(other))
