"""\
Read CSV ballot file (LVR) into object representing a spreadsheet
as cells[row][column]=cellValue plus other bookkeeping instance variables.
"""

from collections import defaultdict
import csv


class LvrSheet():
    """CSV format (per G2016 results; 'day-1-cvr.csv')
 VERY SPARSE in places!

   Row 1:: Headers
     Col 1:: "Cast Vote Record"
     Col 2:: "Precinct"
     Col 3:: "Ballot Style"
     Col 4 to M: RaceName 
        May be blank for VoteFor > 1; treat as RaceName from left non-blank

   Row N::
     Col 1:: CVR (integer)
     Col 2:: Precinct (integer)
     Col 3:: Ballot Style (text)
     Col 4 to M: ChoiceName (corresponding to RaceName in Row 1)
"""
    filename = ''
    cells = defaultdict(dict) # cells[row][column] => value
    max_row = 0
    max_col = 0
    minDataC = 4  # Data COLUMN starts here
    minDataR = 2  # Data ROW starts here
    raceLut = dict() # lut[raceName] = columnNumber (left col of race)
    #! choiceLut = dict() # lut[choiceName] = id
    voteFor = dict() # lut[raceName] = numberToVoteFor; inferred by number
                     # of same race name columns

    def __init__(self, filename):
        """Create: 
cells[row][col]:: sparse 2D matrix representing sheet
raceLut[raceName] = columnNumber (left col of race)
voteFor[raceName] = numberToVoteFor
"""
        self.filename = filename
        #!choice_id = 0
        with open(filename, newline='') as csvfile:
            reader = csv.reader(csvfile, dialect='excel')
            # rid:: rowId, cid:: columnId
            for rid,row in enumerate(reader, 1):
                for cid,val in enumerate(row,1):
                    value = val.strip()
                    if len(value) > 0:
                        self.cells[rid][cid] = value
                        #!if ((rid >= self.minDataR)  and (cid >= self.minDataC)
                        #!    and (value not in self.choiceLut)):
                        #!    self.choiceLut[value] = choice_id
                        #!    choice_id += 1
                        self.max_col = max(self.max_col, cid)
                if (rid >= self.minDataR) and (len(self.cells[rid]) >= self.minDataC):
                    self.max_row = rid
        # Fill RaceName for VoteFor > 1
        raceName = None
        for c in range(self.minDataC, self.max_col + 1):
            if c in self.cells[1]:
                raceName = self.cells[1][c]
                self.voteFor[raceName] = 1
                self.raceLut[raceName] = c
            else:
                self.cells[1][c] = raceName
                self.voteFor[raceName] += 1
        # END: init

    def summary(self):
        print('''
Sheet Summary:
   FILENAME: {} # CSV source
   minDataR: {:2}  Max ROW:  {}
   minDataC: {:2}  Max COL:  {}
   Cell cnt: {}

   Race cnt:     {}
   VoteFor cnts: {}
###################################################################
'''
              .format(self.filename,
                      self.minDataR, self.max_row, 
                      self.minDataC, self.max_col, 
                      sum([len(v) for v in self.cells.values()]),
                      len(self.raceLut),
                      ','.join([str(v) for v in self.voteFor.values()]),
              ))


