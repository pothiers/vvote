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

# Stripped data. Just 400 ballots
mkdir -p ~/.vvote_output 2> /dev/null
LVR="$data/2016GenSampleSet-400.lvr.xlsx"

# simple vote count output (with precincts) to stdout
testCommand vv1_1 "countvote $LVR" "^\#" n

genSOVC="$HOME/.vvote_output/2016GenSampleSet-400.sovc.xlsx"
sovcout="$HOME/.vvote_output/2016GenSampleSet-400.sovc.csv"
testCommand vv2_1 "countvote -f SOVC -t $genSOVC $LVR" "^\#"
xls2csv --transpose $genSOVC $sovcout
testOutput vv2_1_out $sovcout
#testOutput vv2_2_out $genSOVC

racemap="$HOME/.vvote_output/2016GenSampleSet-racemap.csv"
choicemap="$HOME/.vvote_output/2016GenSampleSet-choicemap.csv"
testCommand vv3_1 "genmap $genSOVC $LVR $racemap $choicemap" "^\#"
testOutput vv3_2_out $racemap
testOutput vv3_3_out $choicemap



###########################################
#echo "WARNING: ignoring remainder of tests"
#exit $return_code
###########################################

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

