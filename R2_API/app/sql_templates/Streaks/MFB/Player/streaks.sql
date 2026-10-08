WITH
  AllGames AS (
    SELECT
      player_id,
      player_name,
      TO_DATE(game_date, 'YYYY-MM-DD') AS game_date,
      opponent_team_name,
      team_code,
      team_name,
      opponent_team_code,
      CASE
        WHEN {stat} >= {stat_value}
        THEN 1
        ELSE 0
      END AS meets_criteria
    FROM
      pgs_interim_mfb_pilot
    WHERE
      period_number = 0
      AND period_type = 'REGULAR'
      AND player_id = {player_id}
      AND team_code = {team_code}
  ),
  RankedGames AS (
    SELECT
      player_id,
      player_name,
      game_date,
      meets_criteria,
      opponent_team_name,
      team_code,
      team_name,
      opponent_team_code,
      ROW_NUMBER() OVER (
        PARTITION BY
          player_id
        ORDER BY
          game_date DESC
      ) AS game_number,
      LAG(meets_criteria, 1, 0) OVER (
        PARTITION BY
          player_id
        ORDER BY
          game_date DESC
      ) AS prev_game_met
    FROM
      AllGames
  ),
  Streaks AS (
    SELECT
      player_id,
      player_name,
      game_date,
      opponent_team_name,
      team_code,
      opponent_team_code,
      team_name,
      SUM(
        CASE
          WHEN meets_criteria = 1 AND prev_game_met = 0
          THEN 1
          ELSE 0
        END
      ) OVER (
        PARTITION BY
          player_id
        ORDER BY
          game_date DESC
      ) AS streak_group
    FROM
      RankedGames
    WHERE
      meets_criteria = 1
  ),
  StreakBounds AS (
    SELECT
      player_id,
      player_name,
      streak_group,
      team_name,
      COUNT(*) AS streak_length,
      MIN(game_date) AS start_game_date,
      MAX(game_date) AS end_game_date
    FROM
      Streaks
    GROUP BY
      player_id,
      player_name,
      streak_group,
      team_name
  ),
  FinalStreaks AS (
    SELECT
      sb.player_id,
      sb.player_name,
      sb.streak_length,
      sb.start_game_date,
      sb.end_game_date,
      sb.team_name,
      (
        SELECT
          s.opponent_team_name
        FROM
          Streaks s
        WHERE
          s.player_id = sb.player_id
          AND s.game_date = sb.start_game_date
        LIMIT 1
      ) AS start_opponent,
      (
        SELECT
          s.opponent_team_name
        FROM
          Streaks s
        WHERE
          s.player_id = sb.player_id
          AND s.game_date = sb.end_game_date
        LIMIT 1
      ) AS end_opponent
    FROM
      StreakBounds sb
  )
SELECT
  ROW_NUMBER() OVER () AS id,
  COUNT(*) OVER () AS total_count,
  player_name,
  team_name,
  streak_length,
  start_game_date,
  start_opponent,
  end_game_date,
  end_opponent
FROM
  FinalStreaks
WHERE
  streak_length >= {streak_length}
ORDER BY
  streak_length DESC;