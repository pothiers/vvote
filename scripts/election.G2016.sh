#!/bin/bash -x
eldata=/data/vvote/Elections/G2016
out=$eldata/OUTPUT
cd $out

#! echo "Convert Excel SOVC into CSV $out/export9.sovc.csv"
#! xlsx2csv $eldata/G2016_EXPORT9\ Final.xlsx > $out/export9.sovc.csv
#!
#! echo "Convert Excel LVR into CSV $eldata/OUTPUT/day9.lvr.csv (slow)"
#! xlsx2csv $eldata/Day\ 9\ Final\ CVR\ No\ Images\ -\ Combined.xlsx > $out/day9.lvr.csv

#! echo "Ingest LVR into DB: $out/LVR.db"
#! lvrdb --database $out/LVR.db --incsv $out/day9.lvr.csv --summary
#! #lvrdb --database $out/LVR.db -s

echo "Ingest SOVC into DB: $out/SOVC.db"
sovcdb --database $out/SOVC.db --incsv $out/export9.sovc.csv --summary
#sovcdb --database $out/SOVC.db -s

echo "Generate inital MAP.db initialized with choices/races from LVR/SOVC"
makemapdb -l $out/LVR.db -s $out/SOVC.db --mapdb $out/MAP.db 

echo "Generate mappings between LVR and SOVC"
makemapdb -m $out/MAP.db --calc

makemapdb -m $out/MAP.db --export
# EDIT the RACEMAP.csv and CHOICEMAP.csv files to fix wrong mappings if needed
# Import modified maps
makemapdb -m $out/MAP.db --import RACEMAP.csv CHOICEMAP.csv

# Store summary counts in LVR (using SOVC names)
lvrcnt --lvr $out/LVR.db --map $out/MAP.db
# time: 0:37 sec

~/sandbox/vvote/scripts/compare.sh
