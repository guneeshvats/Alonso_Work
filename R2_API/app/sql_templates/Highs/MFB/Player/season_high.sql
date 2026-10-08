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
RankedBestPerSeason AS (
    SELECT
        *,
        RANK() OVER (
            PARTITION BY stat, season
            ORDER BY value DESC
        ) AS stat_rank
    FROM PlayerStats
),
TopRankedPerSeason AS (
    SELECT *
    FROM RankedBestPerSeason
    WHERE stat_rank = 1
),
FinalWithCount AS (
    SELECT *,
           COUNT(*) OVER() AS total_count
    FROM TopRankedPerSeason
)
SELECT *
FROM FinalWithCount
ORDER BY season, stat;