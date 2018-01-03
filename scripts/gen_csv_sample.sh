#!/bin/bash -e
# PURPOSE: Generate reduced data sample from CSV file (LVR or SOVC)
#
# EXAMPLE:
#
# AUTHORS: S.Pothier

cmd=`basename $0`
dir=`dirname $0`

SCRIPT=$(readlink -f $0)      #Absolute path to this script
SCRIPTPATH=$(dirname $SCRIPT) #Absolute path this script is in

CNT=100
VERBOSE=0

usage="USAGE: $cmd [options] inputCSV outputSample
OPTIONS:
  -c count:: Number of records to keep from inputCSV (default=$CNT)
  -v <verbosity>:: higher number for more output (default=$VERBOSE)

"

while getopts "hp:v:" opt; do
    case $opt in
	h)
            echo "$usage"
            exit 1
            ;;
        v)
            VERBOSE=$OPTARG
            ;;
        c)
            CNT=$OPTARG # Number of records to keep from inputCSV
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


RAC=2 # Required Argument Count
if [ $# -lt $RAC ]; then
    echo "Not enough non-option arguments. Expect at least $RAC."
    echo >&2 "$usage"
    exit 2
fi

CSV=${1:-export999.sovc.csv}
SAMPLE=${2:-export999.sample.sovc.csv}

TOP=4  # number of lines to keep from TOP of CSV
BOT=2  # number of lines to keep from BOTTOM of CSV

##############################################################################
head -n $TOP $CSV > $SAMPLE
head -n -$BOT $CSV | tail -n +$TOP | shuf --head-count=$CNT >> $SAMPLE
tail -n $BOT $CSV >> $SAMPLE
