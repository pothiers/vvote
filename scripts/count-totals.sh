#!/bin/bash -e
# PURPOSE: Count total votes for All Choices, ALL Races
#
# EXAMPLE:
#

SCRIPT=$(greadlink -f $0)        # Absolute path to this script
SCRIPTPATH=$(dirname $SCRIPT)   # Absolute path this script is in


VERBOSE=0
DB="LVR.db"

usage="USAGE: $cmd [options] 
OPTIONS:
  -d <LVR_database>:: LVR DB containing votes (default=$DB)
  -v <verbosity>:: higher number for more output (default=$VERBOSE)
"

while getopts "d:hv:" opt; do
    #! echo "opt=<$opt>"
    case $opt in
        d)
            DB=$OPTARG
            ;;
	h)
            echo "$usage"
            exit 1
            ;;
        v)
            VERBOSE=$OPTARG
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

echo "COUNTING: total votes for All Choices, ALL Races"

SQL="
SELECT count(vote.cvr_id) as Votes,
       race.title as Race, 
       choice.title as Choice 
FROM vote,choice,race 
WHERE vote.choice_id = choice.choice_id 
  AND choice.race_id = race.race_id 
GROUP BY race.column, choice.choice_id;"
sqlite3 -header -column $DB "$SQL"
