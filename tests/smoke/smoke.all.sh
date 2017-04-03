#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Wrapper for smoke test
# EXAMPLE:
#   loadenv lidar
#   $sb/lidar-matcher/test/smoke.sh
#

cmd=`basename $0`
SCRIPT=$(readlink -e $0)     #Absolute path to this script
dir=$(dirname $SCRIPT)       #Absolute path this script is in
REPO=$(dirname $(dirname $dir))  #Absolute path to top of this repo
data="$(dirname $dir)/data"  # ~/sandbox/vvote/tests/data/
origdir=`pwd`
cd $dir
source smoke-lib.sh
cd $dir
sto=$dir

return_code=0
SMOKEOUT="README-smoke-results.txt"

echo "" 
echo "Starting tests in \"$dir\" ..."
echo ""
echo ""
#testCommand gm1_1 "genmap $data/day1-sovc.xlsx $data/day1-cvr.xlsx r.csv c.csv"

OUT="$HOME/.vvote_output"

# Stripped data. Just 400 ballots
mkdir -p $OUT 2> /dev/null
LVR="$data/2016GenSampleSet-400.lvr.xlsx"

PATH=$REPO/sql:$PATH

##############################################################################
LVRDB="$OUT/lvr.db"
testCommand vv0_1 "lvr -d $LVRDB $LVR" "^\#" n
testCommand vv0_2 "dump_vvote_db.sh $LVRDB" "^\#" n

# simple vote count output (with precincts) to stdout
#testCommand vv1_1 "countvote $LVR" "^\#" n
testCommand vv1_2 "race-counts-by-precinct.sh $LVRDB" "^\#" n

# Created an unofficial SOVC file.
genSOVC="$OUT/2016GenSampleSet-400.sovc.xlsx"
sovccsv="$OUT/2016GenSampleSet-400.sovc.csv"
testCommand vv2_1 "countvote -f SOVC -t $genSOVC $LVR" "^\#" n
#xls2csv --transpose $genSOVC $sovccsv
xls2csv $genSOVC $sovccsv
testOutput vv2_2_out $sovccsv
SOVCDB="$OUT/sovc.db"
#testCommand vv2_3 "sovc -d $SOVCDB $genSOVC" "^\#" y
#testCommand vv2_4 "dump_vvote_db.sh $SOVCDB" "^\#" n

#!   ###########################################
#!   echo "WARNING: ignoring remainder of tests"
#!   exit $return_code
#!   ###########################################
#!   
#!   
#!   
#!   testOutput vv2_1_out $sovcout
#!   #testOutput vv2_2_out $genSOVC
#!   
#!   # Create tables to map SOVC titles to LVR titles
#!   racemap="$OUT/2016GenSampleSet-racemap.csv"
#!   choicemap="$OUT/2016GenSampleSet-choicemap.csv"
#!   testCommand vv3_1 "genmap $genSOVC $LVR $racemap $choicemap" "^\#" n
#!   testOutput vv3_2_out $racemap
#!   testOutput vv3_3_out $choicemap
#!   
#!   # COMPARE counted results with official SOVC results.
#!   testCommand vv3_1 "countvote -v --sovc $genSOVC -t counts.txt -c $choicemap -r $racemap $LVR"


#!# almost 40k ballots; mock1.xlsx
#!results1="$sto/mock1-results.out"
#!testCommand vv0_1 "countvote $data/mock1-cvr.xlsx $results1" "^\#" n
#!testOutput vv0_1_out $results1 '^\#' n
#!
#!# almost 50k ballots; time = 60 sec
#!results1="$sto/day1-results.out"
#!testCommand vv1_1 "countvote $data/day1-cvr.xlsx $results1" "^\#" n
#!testOutput vv1_1_out $results1 '^\#' n
#!

#!sovc=$data/day1-sovc.xlsx
#!ballots=$data/day1-cvr.xlsx
#!results1b="$sto/day1-results.out"
#!testCommand vv2_1 "countvote --verbose --sovc $sovc $ballots $results1b"
#!sort $results1b > $results1
#!testOutput vv2_1_out $results1 '^\#' n

##############################################################################

rm $SMOKEOUT 2>/dev/null
if [ $return_code -eq 0 ]; then
  echo ""
  echo "ALL smoke tests PASSED ($SMOKEOUT created)"
  echo "All tests passed on " `date` > $SMOKEOUT
else
  echo "Smoke FAILED (no $SMOKEOUT produced)"
fi


# Don't move or remove! 
cd $origdir
exit $return_code

