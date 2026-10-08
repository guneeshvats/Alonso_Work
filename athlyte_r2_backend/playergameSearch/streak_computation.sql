WITH AllGames AS (
    SELECT
        playerId,
        playerName,
        season,
        TO_DATE(gamedate, 'YYYY-MM-DD') AS gamedate,
        {stat_columns},
        opponentteamname,
        teamcode,
        opponentteamcode,
        CASE WHEN {conditions} THEN 1 ELSE 0 END AS meets_criteria
    FROM {table_name}
    WHERE periodnumber = 0
    AND teamCode = {team_code}
),
RankedGames AS (
    SELECT
        playerId,
        playerName,
        season,
        gamedate,
        {stat_columns},
        meets_criteria,
        opponentteamname,
        teamcode,
        opponentteamcode,
        ROW_NUMBER() OVER (PARTITION BY playerId, season ORDER BY gamedate DESC) AS game_number,
        LAG(meets_criteria, 1, 0) OVER (PARTITION BY playerId, season ORDER BY gamedate DESC) AS prev_game_met
    FROM AllGames
),
Streaks AS (
    SELECT
        playerId,
        playerName,
        season,
        gamedate,
        opponentteamname,
        teamcode,
        opponentteamcode,

        SUM(CASE WHEN meets_criteria = 1 AND prev_game_met = 0 THEN 1 ELSE 0 END)
        OVER (PARTITION BY playerId, season ORDER BY gamedate DESC) AS streak_group
    FROM RankedGames
    WHERE meets_criteria = 1
),
StreakBounds AS (
    SELECT
        playerId,
        playerName,
        season,
        streak_group,
        COUNT(*) AS streak_length,
        MIN(gamedate) AS start_game_date,
        MAX(gamedate) AS end_game_date
    FROM Streaks
    GROUP BY playerId, playerName, season, streak_group
),
FinalStreaks AS (
    SELECT
        sb.playerId,
        sb.playerName,
        sb.season,
        sb.streak_length,
        sb.start_game_date,
        sb.end_game_date,
        -- Fetch the first opponent within the streak
        (SELECT s.opponentteamname FROM Streaks s
         WHERE s.playerId = sb.playerId AND s.season = sb.season
         AND s.gamedate = sb.start_game_date LIMIT 1) AS start_opponent,
        -- Fetch the last opponent within the streak
        (SELECT s.opponentteamname FROM Streaks s
         WHERE s.playerId = sb.playerId AND s.season = sb.season
         AND s.gamedate = sb.end_game_date LIMIT 1) AS end_opponent
    FROM StreakBounds sb
)
SELECT *
FROM FinalStreaks
WHERE streak_length > 1
ORDER BY season DESC, streak_length DESC
LIMIT {limit} OFFSET {skip};

