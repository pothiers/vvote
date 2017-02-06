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
tmpexcel="$HOME/.vvote_output/tmp.xlsx"
sovcout="$HOME/.vvote_output/2016GenSampleSet-sovc.csv"
txtout="$HOME/.vvout_output/2016GenSampleSet-sovc.txt"
testCommand vv2_1 "countvote -f SOVC $data/2016GenSampleSet.xlsx $tmpexcel"
xls2csv $tmpexcel $sovcout
#!testOutput vv2_1_out $sovcout
#!testCommand vv3_1 "countvote $data/2016GenSampleSet.xlsx $txtout"
#!testOutput vv3_1_out $txtcout

###########################################
#echo "WARNING: ignoring remainder of tests"
#exit $return_code
###########################################

# almost 40k ballots; mock1.xlsx
results1="$sto/mock1-results.out"
testCommand vv0_1 "countvote $data/mock1-cvr.xlsx $results1" "^\#" n
testOutput vv0_1_out $results1 '^\#' n

# almost 50k ballots; time = 60 sec
results1="$sto/day1-results.out"
testCommand vv1_1 "countvote $data/day1-cvr.xlsx $results1" "^\#" n
testOutput vv1_1_out $results1 '^\#' n


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

