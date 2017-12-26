#!/bin/bash
# Compare summary tally of LVR to SOVC

out=/data/vvote/Elections/G2016/OUTPUT

echo "NB: Removed records for: OVER VOTES, UNDER VOTES, WRITE-IN"

pushd $out
####################################################################
### LVR
###
# TOTAL votes
echo "Count total votes from LVR per (Race,Choice). NO MAPPING to SOVC names"
sqlite3 -header -csv $out/LVR.db > $out/lvr.total_votes.csv <<EOF
SELECT race as rt, choice as ct, votes
FROM summary_totals
ORDER BY rt, ct;
EOF


#######################################################################
### SOVC
###
# TOTAL votes
echo "Emit TOTAL votes from SOVC"
sqlite3 -header -csv $out/SOVC.db >$out/sovc.total_votes.csv <<EOF
SELECT 
  race.title as rt, 
  choice.title as ct,
  vote.count as votes
FROM vote, choice, race
WHERE 
  vote.choice_id = choice.choice_id 
  AND choice.race_id = race.race_id
  AND vote.precinct_code = 'ZZZ'
GROUP BY rt, ct
ORDER BY rt, ct;
EOF


############################################################################
diff -i --side-by-side $out/lvr.total_votes.csv $out/sovc.total_votes.csv > $out/diff.out

popd
