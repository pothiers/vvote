"""\
Read CSV SOVC file into object representing a spreadsheet.

Model as cells[row][column]=cellValue plus other bookkeeping instance variables.
"""
import logging
from collections import defaultdict
import csv

class SovcSheet():
    """CSV format (per Nov-2017 results; '171107C_EXPORT DAY 2.CSV')
   Row 1:: Race titles (duplicated over columns representing choices)
   Row 2:: party (we don't care)
   Row 3:: Choices
   Row 4 to N-1:: Precinct totals
   Row N:: Grand totals (County totals)
   Row N+1:: "_x001A_"  ??? End of data?

   Col 1:: County Number ('_x001A_' in last row)
   Col 2:: Precinct Code (number)
   Col 3:: Precinct Name (number) or "COUNTY TOTALS"
   Col 4:: "REGISTERED VOTERS - TOTAL" (Row 1)
   Col 5:: Ballots Cast-Total
   Col 6:: Ballots Cast-Blank
   Col 7 to M:: vote counts
"""
    raceR   = 1   # Row containing Race titles
    partyR  = 2   # Row continaing Party name
    choiceR = 3   # Row continaing Choice titles
    minDataC = 7  # Data COLUMN starts here
    minDataR = 4  # Data ROW starts here

    filename = ''
    cells = defaultdict(dict) # cells[row][column] => value
    max_row = 0
    max_col = 0
    choiceLut = dict() # lut[title] = columnNumber
    raceLut = dict() # lut[title] = columnNumber (first column of race)

    def __init__(self, filename):
        """RETURN: sparse 2D matrix representing spreadsheet"""
        self.filename = filename
        with open(filename, newline='') as csvfile:
            sovcreader = csv.reader(csvfile, dialect='excel')
            for ridx,row in enumerate(sovcreader, 1):
                for cidx,val in enumerate(row,1):
                    value = val.strip()
                    if len(value) > 0:
                        self.cells[ridx][cidx] = value
                        self.max_col = max(self.max_col, cidx)
                if (ridx >= self.minDataR) and (len(self.cells[ridx]) > 4):
                    self.max_row = ridx
        # END: init

    def summary(self):
        print('''
Sheet Summary:
   filename: {}

   Max ROW:  {}
   minDataR: {}
   Max COL:  {}
   minDataC: {}
   Cell cnt: {}

   Race cnt:   {}
   Choice cnt: {}
'''
              .format(self.filename,
                      self.max_row, self.minDataR,
                      self.max_col, self.minDataC,
                      sum([len(v) for v in self.cells.values()]),
                      len(self.raceLut), len(self.choiceLut),
              ))

    def get_race_lists(self):
        logging.debug('Get RACE and CHOICE lists')
        race_list = list()   # [(rid, racetitle, numToVoteFor), ...]
        choice_list = list() # [(cid, choicetitle, party), ...]
        column1 = self.minDataC
        while column1 <= self.max_col:
            raceid = column1
            racetitle = self.cells[self.raceR][column1]
            logging.debug('Racetitle={}'.format(racetitle))
            race_list.append((raceid, racetitle, 0))
            self.raceLut[racetitle] = raceid

            # iterate over all columns (choices) of this racetitle
            # range goes off end of columns to aid termination condition
            for column2 in range(column1, self.max_col+2):
                if column2 > self.max_col:  # finished all columns
                    column1 = self.max_col
                    break
                choiceid = column2
                party = self.cells[self.partyR].get(column2,None)
                choicetitle = self.cells[self.choiceR][column2]
                if racetitle == self.cells[self.raceR][column2]:
                    #!logging.debug('Choicetitle={}'.format(choicetitle))
                    choice_list.append((choiceid, choicetitle, raceid, party))
                    #@@@ self.choiceLut[choicetitle] = choiceid
                else: # new race
                    column1 = column2 
                    break
            if column1 == self.max_col:
                break
        return race_list, choice_list
        
    def get_precinct_votes(self):
        "RETURN: dict[(race,choice)] => (count,precinct,regvot,baltot,balblank)"
        logging.debug('Get PRECINCT and VOTE lists')

        precinct_list = list() # [(race_id, choice_id, county, pcode, pname,
                               # regvot, baltot, balblank), ...]
        vote_list = list()     # [(cid, precinct_code, count), ...]
        for col in range(self.minDataC, self.max_col+1):
            racetitle = self.cells[self.raceR][col]
            race_id = self.raceLut[racetitle]
            choicetitle = self.cells[self.choiceR][col]
            #@@@ choice_id = self.choiceLut[choicetitle]
            choice_id = col
            for row in range(self.minDataR, self.max_row+1):
                precinct_list.append(
                    (# race_id,
                     choice_id,
                     self.cells[row][1],   # county number
                     self.cells[row][2],   # precinct code
                     self.cells[row][3],   # precinct name
                     self.cells[row][4],   # reg voters total
                     self.cells[row][5],   # ballots total
                     self.cells[row][6]    # ballots blank
                    ))
                vote_list.append(
                    (choice_id,
                     self.cells[row][2],  # precinct code
                     self.cells[row][col] # vote count
                    ))
        return (precinct_list, vote_list)
