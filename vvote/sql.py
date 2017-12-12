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

lvr_vote = '''SELECT  
  vote.race_id as rid, 
  vote.choice_id as cid, 
  cvr.precinct_code as pc
FROM vote, cvr WHERE vote.cvr_id = cvr.cvr_id
;'''

lvr_choice = 'SELECT choice.choice_id, choice.title FROM choice;'
lvr_race = 'SELECT race.race_id, race.title FROM race;'

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

-- MAP
CREATE TABLE race_map (
   lvr_race_title text,
   sovc_race_title text
);
CREATE TABLE choice_map (
   lvr_choice_title text,
   sovc_choice_title text
);'''

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
    
