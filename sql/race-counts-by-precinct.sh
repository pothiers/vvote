#!/bin/bash
db=$1
race=${2:-"PRESIDENTIAL ELECTOR"}

echo "REPORT: Count of votes per precinct."

read -r -d '' sql <<EOF
SELECT
    race.title as race,
    choice.title as choice,
    vote.count as count,
    vote.precinct_code as precinct
FROM vote, choice, race
WHERE race.title="$race"
    AND race.race_id = choice.race_id
    AND choice.choice_id = vote.choice_id
ORDER BY vote.precinct_code, choice.title;
EOF

#!echo "sql=$sql"
sqlite3 -echo -header -column "$1" "$sql"
