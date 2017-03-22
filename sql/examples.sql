
-- Count by race_title
SELECT
    race.title as race,
    choice.title as choice,
    vote.count as count,
    vote.precinct_code as precinct
FROM vote, choice, race
WHERE race.title="PRESIDENTIAL ELECTOR"
    AND race.race_id = choice.race_id
    AND choice.choice_id = vote.choice_id
ORDER BY vote.precinct_code;
