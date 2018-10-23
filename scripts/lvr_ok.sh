#!/bin/bash -e
# PURPOSE: Sanity check compare of input LVR ("*CVR*.csv") to our DB after import
#
# EXAMPLE:
#   
#
# AUTHORS: S.Pothier

SCRIPT=$(readlink -f $0)        # Absolute path to this script
SCRIPTPATH=$(dirname $SCRIPT)   # Absolute path this script is in

usage="USAGE: $cmd [options] [reportFile]
OPTIONS:
  -p <progress>:: Number of progress updates per second (default=0)
  -v <verbosity>:: higher number for more output (default=0)
"

VERBOSE=0
PROGRESS=0
while getopts "hp:v:" opt; do
    #! echo "opt=<$opt>"
    case $opt in
	h)
            echo "$usage"
            exit 1
            ;;
        v)
            VERBOSE=$OPTARG
            ;;
        p)
            PROGRESS=$OPTARG # how often to report progress
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            exit 1
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            exit 1
            ;;
    esac
done
#echo "OPTIND=$OPTIND"
for (( x=1; x<$OPTIND; x++ )); do shift; done

RAC=0 # Required Argument Count
if [ $# -lt $RAC ]; then
    echo "Not enough non-option arguments. Expect at least $RAC."
    echo >&2 "$usage"
    exit 2
fi

report=${1:-$HOME/logs/foo.report}

#! echo "PROGRESS=$PROGRESS"
#! echo "VERBOSE=$VERBOSE"
#! echo "Remaining arguments:"
#! for arg do echo '--> '"\`$arg'" ; done
##############################################################################

DBFILE="ELECTION.db"
lvrFiles=(/data/vvote/Elections/Primary2018/PCE/vv/P*.csv)
filecnt=${#lvrFiles[@]}
last=`wc -l ${lvrFiles[@]} | tail -1 `
parts=($last)
cnt=${parts[0]}

dataRows=$(($cnt - $filecnt))
dbcnt=`sqlite3 $DBFILE "select count(cvr_id) from cvr;"`

if [ "$dbcnt" -ne "$dataRows" ]; then
    echo "ERROR: Number of Cast Vote Records do not agree."
    echo "  per LVR files: $dataRows; from (${#lvrFiles[@]})"
    echo "  per DB ($DBFILE): $dbcnt"
else
    echo "CVR counts match"
fi
