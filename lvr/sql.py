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
CREATE TABLE choice (
   choice_id integer primary key,
   title text,
   race_id integer,
   party text
);
CREATE TABLE cvr (
   cvr_id integer primary key,
   precinct_code integer,
   ballot_style text
);

CREATE TABLE vote (
   cvr_id integer,
   choice_id integer
);


CREATE TABLE summary_totals (
   race text,
   choice text,
   votes integer
);

CREATE TABLE precinct (
  choice_id integer,
  county_number,
  precinct_code,  -- id
  precinct_name,
  registered_voters integer,
  ballots_cast_total integer,
  ballots_cast_blank integer
);
'''
