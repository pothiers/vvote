#!/bin/bash -e
# PURPOSE: Count total votes for All Choices, All Races, Selected Precinct
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

RAC=1 # Required Argument Count
if [ $# -lt $RAC ]; then
    echo "Not enough non-option arguments. Expect at least $RAC."
    echo >&2 "$usage"
    exit 2
fi

#RACE="U.S. SENATOR DEM"
PRECINCT="$@"


##############################################################################

echo "COUNTING: Count total votes for All Choices, All Races, Precinct=$PRECINCT"

SQL="
SELECT count(vote.cvr_id) as Votes,
       cvr.precinct as Precinct,
       choice.title as Choice,
       race.title as Race
FROM vote,choice,race,cvr 
WHERE vote.choice_id = choice.choice_id 
  AND choice.race_id = race.race_id 
  AND vote.cvr_id = cvr.cvr_id 
  AND cvr.precinct = $PRECINCT
GROUP BY race.column, choice.choice_id;"

sqlite3 -header -column $DB "$SQL"
