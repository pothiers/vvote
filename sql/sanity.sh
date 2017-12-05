# Count Precincts (numRows - 3)
sqlite3 SOVC.db "SELECT count(distinct(precinct_name)) from precinct;"
# Count Choices (numRows - 6)
sqlite3 SOVC.db "SELECT count(choice_id) FROM choice;"

### Totals balance
# Grand totals of all columns per Official
sqlite3 -header -column SOVC.db "SELECT race.title, choice.title, vote.count AS count FROM vote,race,choice WHERE precinct_code='ZZZ' AND choice.choice_id = vote.choice_id AND race.race_id = choice.race_id ORDER BY race.title ASC, choice.title ASC;"
