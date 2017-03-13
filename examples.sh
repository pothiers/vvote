#!/bin/bash

data="$HOME/sandbox/vvote/tests/data"

# Activate env and install latest
source ~/sandbox/vvote/venv/bin/activate
cd ~/sandbox/vvote
#! git pull
./install.sh

########################
## Sample invocations

# Create mappings for RACE and CHOICE titles (SOVC to LVR)
genmap -v $data/day1-sovc.xlsx $data/day1-lvr.xlsx rm.csv cm.csv


# Tally votes. Output as SOVC format. The SOVC will be the calculated
# tallys that we can compare to the official SOVC except that the RACE
# and CHOICE strings may differ somewhat.
countvote --format SOVC $data/2016GenSampleSet-400.cvr.xlsx 2016GenSampleSet-400.sovc.xlsx 

# UNDER-CONSTRUCTION!!!
comparesovc --racemap rm.csv --choicemap cm.csv 2016GenSampleSet-400.sovc.xlsx $data/2016GenSampleSet-400.sovc.xlsx
