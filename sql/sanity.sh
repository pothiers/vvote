##############################################################################
### SOVC
###

# Count Precincts (numRows - 3)
sqlite3 SOVC.db "SELECT count(distinct(precinct_name)) from precinct;"
# Count Choices (numRows - 6)
sqlite3 SOVC.db "SELECT count(choice_id) FROM choice;"

### Totals balance
# Grand totals of all columns per Official
sqlite3 -header -column SOVC.db "SELECT race.title, choice.title, vote.count AS count FROM vote,race,choice WHERE precinct_code='ZZZ' AND choice.choice_id = vote.choice_id AND race.race_id = choice.race_id ORDER BY race.title ASC, choice.title ASC;"


##############################################################################
### LVR  (day-1-cvr.csv)
###

# Count CVRs (numRows - 1)
sqlite3 LVR.db "SELECT count() FROM cvr;"
# 49418

# Count Races; (87) < (numCols(113) - 3)
sqlite3 LVR.db "SELECT count() FROM race;"
# 87

# Count max num choices over all races; votesAllowed(110) == (numCols(113) - 3)
sqlite3 LVR.db "SELECT SUM(votesAllowed) FROM race;"
# 110

# !!!!!!!!! ERROR;  NOT 144 <= 110 +
#   2 extra "choices" are: Write-in, undervote
#   2 erroneous extra "choices": YESx3
# Count distinct choice TITLES; numDistinctChoiceTitles <= maxNumChoices
sqlite3 LVR.db "SELECT count(distinct(title)) FROM choice;"
# 144     
#  OH!! The number of available choices for Race can be more than votesAllowed.
#  VotesAllowed just limits the number of choices for ONE ballot.


# Is votesAllowed >=  number of choices for every race?
sqlite3 LVR.db "SELECT race.*,  count(choice.choice_id) FROM race left join choice on race.race_id = choice.race_id group by race.title;"
## race_id=59, votesAllowed=3, count(choice.choice_id)=9   !!!!


# Count max num votes;
#   numVotes(1,984,942) <= numCVR(49,418) * maxChoices(110) = 5,435,980
sqlite3 LVR.db "SELECT count() FROM vote;"
# 1984942

# Count num chosen from all ballots for each race
sqlite3  LVR.db <<EOF
.headers on
.mode column
.width 50 5 5
SELECT  race.title, race.votesAllowed, count(choice.choice_id) as numChosen FROM race LEFT JOIN choice, race_choice ON race_choice.race_id = race.race_id AND race_choice.choice_id = choice.choice_id group by race.title;
EOF



# votes, one line of CSV
sqlite3  LVR.db <<EOF
.headers on
.mode column
.width 7 50 50 2
SELECT cvr.cvr_id, race.title, choice.title, race.votesAllowed as numV
FROM vote, choice, race, cvr
WHERE vote.cvr_id=176882 
  AND vote.cvr_id=cvr.cvr_id
  AND vote.race_id = race.race_id  
  AND vote.choice_id = choice.choice_id 
ORDER BY vote.cvr_id ASC, race.title ASC;
EOF

# 
SELECT  race.race_id, race.votesAllowed as numV, choice.title
FROM choice LEFT JOIN race, vote
ON  vote.cvr_id=176882 AND vote.race_id = race.race_id AND vote.choice_id = choice.choice_id
ORDER BY vote.cvr_id ASC, race.title ASC LIMIT 113;



SELECT  race.race_id, race.votesAllowed as numV, choice.title
FROM choice LEFT JOIN race, vote
ON  vote.cvr_id=176882 AND vote.race_id = race.race_id AND vote.choice_id = choice.choice_id
ORDER BY vote.cvr_id ASC, race.title ASC LIMIT 113;


# votes (for export to CSV)
SELECT cvr.cvr_id as cid, cvr.precinct_code as pc, ballot_style as ball,
  choice.title as ct, vote.race_id as rid
FROM vote, choice, cvr
WHERE vote.cvr_id = cvr.cvr_id  AND vote.choice_id = choice.choice_id
ORDER BY vote.cvr_id ASC, vote.race_id ASC
LIMIT 300;
