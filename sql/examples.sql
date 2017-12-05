
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


-- Show all undervotes (race,choice,count) for each precinct
SELECT race.title, choice.title, vote.count
FROM race, choice, vote
WHERE vote.choice_id=choice.choice_id
    AND race.race_id=choice.race_id
    AND choice.title like "%undervote%"
ORDER BY race.title ;


-- List Choices
SELECT race.title, choice.title FROM choice, race
WHERE race.race_id = choice.race_id ORDER BY race.title;


