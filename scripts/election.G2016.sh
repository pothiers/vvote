#!/bin/bash
#
# This is the complete flow using vvote programs to process G2016
# election results. The inputs are the Excel files were were given.
# Several intermediate files are created and used.  Many of these
# provide "touch points" for either analysis (e.g. the *.db files) or
# correction of Race or Choice mapping (e.g. *MAP.csv files). The
# final output is diff.out, which compares LVR summary to SOVC.
#
#  Inputs:
#    G2016_EXPORT9 Final.xlsx
#    Day 9 Final CVR No Images - Combined.xlsx
#
#  OUTPUTS:
#    day9.lvr.csv
#    export9.sovc.csv
#
#    LVR.db
#    MAP.db
#    SOVC.db
#
#    RACEMAP.csv
#    CHOICEMAP.csv
#
#    lvr.total_votes.csv
#    sovc.total_votes.csv
#    diff.out


eldata=/data/vvote/Elections/G2016
out=$eldata/OUTPUT
cd $out

echo "## Convert Excel SOVC into CSV $out/export9.sovc.csv"
xlsx2csv $eldata/G2016_EXPORT9\ Final.xlsx > $out/export9.sovc.csv

echo "## Convert Excel LVR into CSV $eldata/OUTPUT/day9.lvr.csv (slow)"
xlsx2csv $eldata/Day\ 9\ Final\ CVR\ No\ Images\ -\ Combined.xlsx > $out/day9.lvr.csv

echo "## Ingest LVR into DB: $out/LVR.db"
lvrdb --database $out/LVR.db --incsv $out/day9.lvr.csv
#lvrdb --database $out/LVR.db --summary

echo "## Ingest SOVC into DB: $out/SOVC.db"
sovcdb --database $out/SOVC.db --incsv $out/export9.sovc.csv 
#sovcdb --database $out/SOVC.db --summary

echo "## Generate inital MAP.db initialized with choices/races from LVR/SOVC"
makemapdb --new -l $out/LVR.db -s $out/SOVC.db --mapdb $out/MAP.db 

echo "## Generate mappings between LVR and SOVC"
makemapdb -m $out/MAP.db --calc

echo "## Export RACE and CHOICE mappings"
makemapdb -m $out/MAP.db --export
#
# EDIT the RACEMAP.csv and CHOICEMAP.csv files to fix wrong mappings if needed
#
echo "## Import possibly modified (RACE and) CHOICE mappings"
makemapdb -m $out/MAP.db --import RACEMAP.csv CHOICEMAP.csv

echo "## Store summary counts in LVR (using SOVC names)"
time lvrcnt --lvr $out/LVR.db --map $out/MAP.db
# time: 0:37 sec

echo "## Compare LVR summary to SOVC"
~/sandbox/vvote/scripts/compare.sh
