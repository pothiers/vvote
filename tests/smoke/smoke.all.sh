#!/bin/bash
# AUTHORS:    S. Pothier
# PURPOSE:    Wrapper for smoke test
# EXAMPLE:
#   loadenv lidar
#   $sb/lidar-matcher/test/smoke.sh
#

cmd=`basename $0`
SCRIPT=$(readlink -e $0)     #Absolute path to this script
dir=$(dirname $SCRIPT) #Absolute path this script is in
data="$(dirname $dir)/data"
origdir=`pwd`
cd $dir

source smoke-lib.sh
return_code=0
SMOKEOUT="README-smoke-results.txt"

echo ""
echo "Starting tests in \"$dir\" ..."
echo ""
echo ""


# almost 50k ballots; time = 60 sec
results1="$sto/day1-results.out"
testCommand vv1_1 "countvote $data/day-1-cvr.xlsx $results1" "^\#" y
testOutput out $results1 '^\#' n


###########################################
#! echo "WARNING: ignoring remainder of tests"
#! exit $return_code
###########################################


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

