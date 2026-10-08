WITH PlayerStats AS (
    SELECT
        stat,
        value,
        season,
        game_date,
        opponent_team_name
    FROM pgs_interim_mfb_pilot_unpivot
    WHERE player_id = '{player_id}'
      AND value IS NOT NULL
),
RankedBestCareer AS (
    SELECT
        *,
        RANK() OVER (
            PARTITION BY stat
            ORDER BY value DESC
        ) AS stat_rank
    FROM PlayerStats
),
TopRanked AS (
    SELECT *
    FROM RankedBestCareer
    WHERE stat_rank = 1
),
FinalWithCount AS (
    SELECT *,
           COUNT(*) OVER() AS total_count
    FROM TopRanked
)
SELECT *
FROM FinalWithCount
ORDER BY stat;

