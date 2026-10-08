WITH AllGames AS (
    SELECT 
        playerId,
        playername,
        season,
        TO_DATE(gamedate, 'YYYY-MM-DD') AS gamedate,
        opponentteamname,
        teamcode,
        teamname,
        opponentteamcode,
        CASE WHEN {conditions} THEN 1 ELSE 0 END AS meets_criteria
    FROM {table_name}
    WHERE periodnumber = 0
),
RankedGames AS (
    SELECT 
        playerId,
        playername,
        season,
        gamedate,
        meets_criteria,
        opponentteamname,
        teamcode,
        teamname,
        opponentteamcode,
        ROW_NUMBER() OVER (PARTITION BY playerId, season ORDER BY gamedate DESC) AS game_number,
        LAG(meets_criteria, 1, 0) OVER (PARTITION BY playerId, season ORDER BY gamedate DESC) AS prev_game_met
    FROM AllGames
),
Streaks AS (
    SELECT 
        playerId,
        playername,
        season,
        gamedate,
        opponentteamname,
        teamcode,
        opponentteamcode,
        teamname,
        SUM(CASE WHEN meets_criteria = 1 AND prev_game_met = 0 THEN 1 ELSE 0 END)
        OVER (PARTITION BY playerId, season ORDER BY gamedate DESC) AS streak_group
    FROM RankedGames
    WHERE meets_criteria = 1
),
StreakBounds AS (
    SELECT 
        playerId,
        playername,
        season,
        streak_group,
        teamname,
        COUNT(*) AS streak_length,
        MIN(gamedate) AS start_game_date,
        MAX(gamedate) AS end_game_date
    FROM Streaks
    GROUP BY playerId, playername, season, streak_group, teamname
),
FinalStreaks AS (
    SELECT 
        sb.playerId,
        sb.playername,
        sb.season,
        sb.streak_length,
        sb.start_game_date,
        sb.end_game_date,
        sb.teamname,
        (SELECT s.opponentteamname FROM Streaks s
        WHERE s.playerId = sb.playerId AND s.season = sb.season 
        AND s.gamedate = sb.start_game_date LIMIT 1) AS start_opponent,
        (SELECT s.opponentteamname FROM Streaks s
        WHERE s.playerId = sb.playerId AND s.season = sb.season 
        AND s.gamedate = sb.end_game_date LIMIT 1) AS end_opponent
    FROM StreakBounds sb
)
SELECT ROW_NUMBER() OVER () AS id, playername, teamname, season, streak_length, start_game_date, start_opponent, end_game_date, end_opponent
FROM FinalStreaks
WHERE streak_length >= {streak_length}
ORDER BY {final_sort_by} {final_sort_order}
LIMIT {limit} OFFSET {offset};
