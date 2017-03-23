#!/bin/bash
db=$1

#echo "REPORT: Count of votes by race (total over all precincts)."

read -r -d '' sql <<EOF
SELECT
    sum(vote.count) as COUNT,
    race.title as RACE,
    choice.title as CHOICE
FROM vote, choice, race
WHERE race.race_id = choice.race_id
    AND choice.choice_id = vote.choice_id
GROUP BY choice.choice_id
ORDER BY race.title, count DESC, choice.title;
EOF

#!echo "sql=$sql"
sqlite3 -header  "$db" "$sql"
