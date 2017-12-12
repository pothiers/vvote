#!/bin/bash
# Compare summary tally of LVR to SOVC

out=/data/vvote/Elections/G2016/OUTPUT

echo "NB: Removed records for: OVER VOTES, UNDER VOTES, WRITE-IN"

###################
echo "Count votes from LVR per (precinct,Race,Choice). Raw data for SOVC"
sqlite3 -header -csv $out/LVR.db > $out/lvr.votes.csv <<EOF
attach 'MAP.db' as db2;
SELECT 
  cvr.precinct_code as pc, 
  db2.race_map.sovc_race_title as rt, 
  db2.choice_map.sovc_choice_title as ct,
  count(vote.cvr_id) as votes
FROM vote, cvr, race, choice, db2.choice_map, db2.race_map
WHERE vote.cvr_id = cvr.cvr_id 
  AND vote.race_id = race.race_id
  AND vote.choice_id = choice.choice_id
  AND db2.choice_map.lvr_choice_title = choice.title
  AND db2.race_map.lvr_race_title = race.title
  AND ct <> 'OVER VOTES'
  AND ct <> 'UNDER VOTES'
  AND ct <> 'WRITE-IN'
GROUP BY pc, rt, ct
ORDER BY CAST(pc AS INTEGER), rt, ct;
EOF

###################
echo "Emit votes from SOVC"
sqlite3 -header -csv $out/SOVC.db >$out/sovc.votes.csv <<EOF
SELECT vote.precinct_code as pc, race.title as rt, choice.title as ct,
  vote.count as votes
FROM vote, choice, race
WHERE vote.choice_id = choice.choice_id AND choice.race_id = race.race_id
  AND pc <> 'ZZZ'
  AND votes <> 0
  AND ct <> 'OVER VOTES'
  AND ct <> 'UNDER VOTES'
  AND ct <> 'WRITE-IN'
GROUP BY pc, rt, ct
ORDER BY CAST(pc AS INTEGER), rt, ct;
EOF

###################
diff -i --side-by-side $out/lvr.votes.csv $out/sovc.votes.csv > $out/diff.out
