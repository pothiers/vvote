"""\
SQL commands used in the python code.  
All tables in single SQLITE file (for one election).
"""

lvr_schema = '''

CREATE TABLE source (
   filename text -- e.g LVR: P-2018-CRV-2.csv
);
CREATE TABLE race (
   race_id integer primary key,
   title text,
   column integer,
   num_to_vote_for integer -- aka. votesAllowed 
);
CREATE TABLE cvr (
   cvr_id integer primary key,
   precinct integer,
   ballot_style text
);
CREATE TABLE choice (
   choice_id integer primary key,
   title text,
   race_id integer,
   party text
);

CREATE TABLE vote (
   cvr_id integer,
   choice_id integer
);
'''

race_lut = 'SELECT race_id, title, column, num_to_vote_for FROM race;'
choice_lut = 'SELECT choice_id, title, race_id, party FROM choice;'

# c.execute(count_candidate, choice_title)
count_candidate = '''
SELECT 
   count(vote.cvr_id) 
FROM
   vote, choice
WHERE
     vote.choice_id = choice.choice_id
 AND choice.title = ?;
'''
##  ok
# SELECT count(vote.cvr_id) FROM vote,choice WHERE vote.choice_id = choice.choice_id AND choice.title = "ABBOUD, DEEDRA";


choices_in_race = '''
SELECT 
   race.title, choice.title
FROM
   choice, race
WHERE
     choice.race_id = race.race_id
 AND race.title = ?;
'''
### ok
# SELECT race.title, choice.title FROM choice,race WHERE choice.race_id = race.race_id AND race.title = "U.S. SENATOR DEM";

count_by_Xrace_by_choice = '''
SELECT count(vote.cvr_id), race.title, choice.title 
FROM vote,choice,race 
WHERE vote.choice_id = choice.choice_id 
  AND race.race_id = choice.race_id 
  AND race.title = ?
GROUP BY choice.choice_id;
'''
# good EXCEPT "Write-in" is low


# COUNT per RACE per CANDIDATE
#   spotcheck look good EXCEPT "Write-in" is low
#   File contains what looks like images for write-ins in some places
#     AND "Write-in" as text in others.
# sqlite3 -header -column LVR.db 'SELECT count(vote.cvr_id), race.title as "rTitle", choice.title as "cTitle" FROM vote,choice,race WHERE vote.choice_id = choice.choice_id AND choice.race_id = race.race_id GROUP BY race.column, choice.choice_id;'

# All Races, All Candidates, by SELECTED Precinct 
# SELECT count(vote.cvr_id), cvr.precinct as Precinct, race.title as "rTitle", choice.title as "cTitle" FROM vote,choice,race,cvr WHERE vote.choice_id = choice.choice_id AND choice.race_id = race.race_id AND vote.cvr_id = cvr.cvr_id AND cvr.precinct = 249 GROUP BY race.column, choice.choice_id;
