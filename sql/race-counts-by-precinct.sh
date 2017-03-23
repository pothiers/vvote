#!/bin/bash
db=$1
#race=${2:-"PRESIDENTIAL ELECTOR"}

#echo "REPORT: Count of votes per precinct."

read -r -d '' sql <<EOF
SELECT
    vote.precinct_code as precinct,
    vote.count as count,
    race.title as race,
    choice.title as choice
FROM vote, choice, race
WHERE race.race_id = choice.race_id
    AND choice.choice_id = vote.choice_id
ORDER BY vote.precinct_code, race.title, choice.title;
EOF

#!echo "sql=$sql"
sqlite3 -header  "$db" "$sql"

