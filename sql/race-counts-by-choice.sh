#!/bin/bash
db=$1
race=${2:-"PRESIDENTIAL ELECTOR"}

echo "REPORT: Count of votes per choice (over all precincts)."

read -r -d '' sql <<EOF
SELECT
    race.title as race,
    choice.title as choice,
    SUM(vote.count)
FROM vote, choice, race
WHERE race.title="$race"
    AND race.race_id = choice.race_id
    AND choice.choice_id = vote.choice_id
    AND vote.precinct_code != "ALL"
GROUP BY choice.title
ORDER BY choice.title;
EOF

#!echo "sql=$sql"
sqlite3 -echo -header -column "$1" "$sql"
