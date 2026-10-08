WITH AllGames AS (
    SELECT 
        game_date,
        opponent_team_name,
        team_code,
        team_name,
        opponent_team_code,
        CASE WHEN {conditions} THEN 1 ELSE 0 END AS meets_criteria
    FROM {table_name}
    WHERE period_number = 0
    AND period_type = 'REGULAR'
    AND team_Code = {team_code}
),
RankedGames AS (
    SELECT
        team_name,
        game_date,
        meets_criteria,
        opponent_team_name,
        team_code,
        opponent_team_code,
        ROW_NUMBER() OVER (PARTITION BY team_code ORDER BY game_date DESC) AS game_number,
        LAG(meets_criteria, 1, 0) OVER (PARTITION BY team_code ORDER BY game_date DESC) AS prev_game_met
    FROM AllGames
),
Streaks AS (
    SELECT 
        game_date,
        opponent_team_name,
        team_code,
        opponent_team_code,
        team_name,
        SUM(CASE WHEN meets_criteria = 1 AND prev_game_met = 0 THEN 1 ELSE 0 END)
        OVER (PARTITION BY team_code ORDER BY game_date DESC) AS streak_group
    FROM RankedGames
    WHERE meets_criteria = 1
),
StreakBounds AS (
    SELECT 
        team_code,
        streak_group,
        team_name,
        COUNT(*) AS streak_length,
        MIN(game_date) AS start_game_date,
        MAX(game_date) AS end_game_date
    FROM Streaks
    GROUP BY team_code, team_name, streak_group
),
FinalStreaks AS (
    SELECT 
        sb.team_code,
        sb.team_name,
        sb.streak_length,
        sb.start_game_date,
        sb.end_game_date,
         (SELECT s.opponent_team_name FROM Streaks s
         WHERE s.team_code = sb.team_code AND s.game_date = sb.start_game_date LIMIT 1) AS start_opponent,
        (SELECT s.opponent_team_name FROM Streaks s
         WHERE s.team_code = sb.team_code AND s.game_date = sb.end_game_date LIMIT 1) AS end_opponent
    FROM StreakBounds sb
)
SELECT ROW_NUMBER() OVER () AS id, team_name, streak_length, start_game_date, start_opponent, end_game_date, end_opponent
FROM FinalStreaks
WHERE streak_length >= {streak_length}
ORDER BY {final_sort_by} {final_sort_order}
LIMIT {limit} OFFSET {offset};
