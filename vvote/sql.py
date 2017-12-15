##############################################################################
### LVR
###
lvr_schema = '''
CREATE TABLE source (
   filename text
);
CREATE TABLE race (
   race_id integer primary key,
   votesAllowed integer,
   title text
);
CREATE TABLE choice (
   choice_id integer primary key,
   title text
);
CREATE TABLE cvr (
   cvr_id integer primary key,
   precinct_code integer,
   ballot_style text
);
CREATE TABLE vote (
   cvr_id integer,
   race_id integer,
   choice_id integer
);
'''

###################
lvr_choice = 'SELECT choice.choice_id, choice.title FROM choice;'
lvr_race = 'SELECT race.race_id, race.title FROM race;'

###################
# Votes
lvr_vote = '''SELECT  
  vote.race_id as rid, 
  vote.choice_id as cid, 
  cvr.precinct_code as pc
FROM vote, cvr WHERE vote.cvr_id = cvr.cvr_id
;'''

lvr_precinct_votes = '''
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
ORDER BY CAST(pc AS INTEGER), rt, ct; '''

lvr_total_votes = '''
attach 'MAP.db' as db2;
SELECT 
  db2.race_map.sovc_race_title as rt, 
  db2.choice_map.sovc_choice_title as ct,
  count(vote.choice_id) as votes
FROM vote, race, choice, db2.choice_map, db2.race_map
WHERE 
  vote.race_id = race.race_id
  AND vote.choice_id = choice.choice_id
  AND db2.choice_map.lvr_choice_title = choice.title
  AND db2.race_map.lvr_race_title = race.title
  AND ct <> 'OVER VOTES'
  AND ct <> 'UNDER VOTES'
  AND ct <> 'WRITE-IN'
GROUP BY rt, ct
ORDER BY rt, ct; '''

##############################################################################
### SOVC
###
sovc_schema = '''
CREATE TABLE source (
   filename text
);
CREATE TABLE race (
   race_id integer primary key,
   title text,
   num_to_vote_for integer
);
CREATE TABLE choice (
   choice_id integer primary key,
   title text,
   race_id integer,
   party text
);
CREATE TABLE precinct (
  race_id integer,
  choice_id integer,
  county_number,
  precinct_code integer,  -- id
  precinct_name,
  registered_voters integer,
  ballots_cast_total integer,
  ballots_cast_blank integer
);
CREATE TABLE vote (
  choice_id integer,
  precinct_code,
  count integer
);
'''

###################
sovc_choice = '''SELECT 
  race.title AS rt,   
  race.num_to_vote_for as nv,
  choice.title AS ct,  
  choice.choice_id as cid
FROM choice, race
WHERE race.race_id = choice.race_id 
ORDER BY race_id ASC, choice_id ASC;'''

sovc_precinct = '''SELECT 
  precinct.county_number AS county,
  precinct.precinct_code AS pcode,
  precinct.precinct_name AS pname,
  precinct.registered_voters AS totvot,
  precinct.ballots_cast_total AS totbal,
  precinct.ballots_cast_blank AS blankbal,
FROM precinct 
ORDER BY precinct.county_number ASC, pcode ASC;'''

sovc_race = '''SELECT vote.count AS count
FROM vote, precinct
WHERE vote.precinct_code = precinct.precinct_code
ORDER BY race_id
;
'''

###################
# Votes
sovc_precinct_votes = '''
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
ORDER BY CAST(pc AS INTEGER), rt, ct;'''

sovc_total_votes = '''
SELECT vote.precinct_code as pc, race.title as rt, choice.title as ct,
  vote.count as votes
FROM vote, choice, race
WHERE vote.choice_id = choice.choice_id AND choice.race_id = race.race_id
  AND pc = 'ZZZ'
  AND votes <> 0
  AND ct <> 'OVER VOTES'
  AND ct <> 'UNDER VOTES'
  AND ct <> 'WRITE-IN'
GROUP BY pc, rt, ct
ORDER BY CAST(pc AS INTEGER), rt, ct;'''

##############################################################################
### MAP
###
map_schema = '''
CREATE TABLE source (
   map_filename text,
   lvr_filename text,
   sovc_filename text
);
-- LVR
CREATE TABLE lvr_race (
   race_id integer primary key,
   title text
);
CREATE TABLE lvr_choice (
   choice_id integer primary key,
   title text
);
CREATE TABLE lvr_rc (
   race_id integer,
   choice_id integer
);
-- SOVC
CREATE TABLE sovc_race (
   race_id integer primary key,
   title text
);
CREATE TABLE sovc_choice (
   choice_id integer primary key,
   title text
);
CREATE TABLE SOVC_rc (
   race_id integer,
   choice_id integer
);
-- Map LVR Race titles to SOVC race titles
CREATE TABLE race_map (
   confidence real, -- in range [0.0,1.0]; similarity metric; 1.0 == identical
   lvr_race_id integer,
   lvr_race_title text,
   sovc_race_id integer,
   sovc_race_title text
);
-- Map LVR Choice titles to SOVC Choice titles
CREATE TABLE choice_map (
   confidence real, -- in range [0.0,1.0]; similarity metric; 1.0 == identical
   lvr_choice_id integer,
   lvr_choice_title text,
   sovc_choice_id integer,
   sovc_choice_title text
);'''

race_map = '''SELECT
   confidence,
   lvr_race_id AS lid,
   lvr_race_title AS lti,
   sovc_race_id AS sid,
   sovc_race_title AS sti
FROM race_map ORDER BY lti;'''

choice_map = '''SELECT
   confidence,
   lvr_choice_id AS lid,
   lvr_choice_title AS lti,
   sovc_choice_id AS sid,
   sovc_choice_title AS sti
FROM choice_map ORDER BY lti;'''


map_lvr_rc = '''SELECT DISTINCT 
  race.title AS rt, 
  race.race_id AS rid, 
  choice.title AS ct,
  choice.choice_id AS cid
FROM vote,race,choice 
WHERE vote.race_id = race.race_id AND vote.choice_id = choice.choice_id 
ORDER BY rt, ct;'''

map_sovc_rc = '''SELECT DISTINCT 
  race.title AS rt, 
  race.race_id AS rid, 
  choice.title AS ct,
  choice.choice_id AS cid 
FROM precinct,race,choice 
WHERE precinct.race_id = race.race_id AND precinct.choice_id = choice.choice_id 
ORDER BY rt, ct;'''

map_tpl = '''SELECT 
  {src}_race.race_id     as rid,
  {src}_race.title       as rti,
  {src}_choice.choice_id as cid,
  {src}_choice.title     as cti
FROM {src}_race, {src}_choice, {src}_rc
WHERE {src}_rc.race_id = rid AND {src}_rc.choice_id = cid;'''
    
