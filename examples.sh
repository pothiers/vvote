#!/bin/bash

data="$HOME/sandbox/vvote/tests/data"
data2="/data/vvote"
out="$HOME/.vvote_output"

LVR="$data/2016GenSampleSet-400.lvr.xlsx"
SOVC="$data2/G2016_EXPORT1.xlsx"

# Activate env and install latest
source ~/sandbox/vvote/venv/bin/activate
cd ~/sandbox/vvote
#! git pull
./install.sh

########################
## See also: ~/sandbox/vvote/tests/smoke/smoke.all.sh

## Sample invocations

xlsx2csv /data/vvote/Elections/G2016/G2016_EXPORT9\ Final.xlsx > export9.sovc.csv
xlsx2csv /data/vvote/Elections/G2016/Day\ 9\ Final\ CVR\ No\ Images\ -\ Combined.xlsx > day9.lvr.csv

# INGEST LVR
lvrdb day-1-cvr.csv  # => LVR.db
# lvr2csv LVR.db lvr.csv

# INGEST SOVC
sovcdb G2016_EXPORT1.csv  # => SOVC.db

# create MAP db
makemapdb -l LVR.db -s SOVC.db

# Generate mappings between LVR and SOVC
makemapdb --calc

##############################################################################

lvr $LVR    
sovc $SOVC  # => SOVC.db



# Create mappings for RACE and CHOICE titles (SOVC to LVR)
genmap -v $data/day1-sovc.xlsx $data/day1-lvr.xlsx rm.csv cm.csv

genmap -v $SOVC  "$data2/Day 1 CVR no Images.xlsx"  day1race.csv day1choice.csv

libreoffice5.1 racematrix.csv choicematrix.csv day1race.csv day1choice.csv

countvote -v --format text $data/day1-lvr.xlsx day1.txt

# Tally votes. Output as SOVC format. The SOVC will be the calculated
# tallys that we can compare to the official SOVC except that the RACE
# and CHOICE strings may differ somewhat.
countvote --format SOVC $LVR 2016GenSampleSet-400.sovc.xlsx 

# UNDER-CONSTRUCTION!!!
# see vvote/sovc.py
countvote -v --sovc  $SOVC "$data2/Day 1 CVR no Images.xlsx" day1.txt

comparesovc --racemap rm.csv --choicemap cm.csv 2016GenSampleSet-400.sovc.xlsx $data/2016GenSampleSet-400.sovc.xlsx

