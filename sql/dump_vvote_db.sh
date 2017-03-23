#!/bin/bash
db=$1
echo "REPORT: All contents of database: $db"

read -r -d '' sql <<EOF
SELECT * FROM source   ORDER BY filename;
SELECT * FROM race     ORDER BY race_id;
SELECT * FROM choice   ORDER BY choice_id, race_id;
SELECT * FROM precinct ORDER BY precinct_code, race_id;
SELECT * FROM vote     ORDER BY choice_id,precinct_code;
EOF

#!echo "sql=$sql"
sqlite3 -echo -header $db "$sql"
