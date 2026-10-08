WITH RankedGames AS (
    SELECT
        stat,
        value,
        season,
        player_id,
        player_name,
        RANK() OVER (PARTITION BY stat ORDER BY value DESC) AS rank
    FROM pss_interim_mfb_pilot_unpivot
    WHERE team_code = {team_code}
      AND value IS NOT NULL
),
ValueToNextHigherMap AS (
    SELECT
        stat,
        value AS current_value,
        LAG(value) OVER (PARTITION BY stat ORDER BY value DESC) AS next_rank_value
    FROM (SELECT DISTINCT stat, value FROM RankedGames) AS dv
),
JoinedData AS (
    SELECT
        rg.*,
        vmap.next_rank_value
    FROM RankedGames rg
    LEFT JOIN ValueToNextHigherMap vmap
        ON rg.stat = vmap.stat AND rg.value = vmap.current_value
    WHERE rg.player_id = '{player_id}'
      AND rg.rank <= {rank_threshold}
),
FinalWithCount AS (
    SELECT *,
           COUNT(*) OVER() AS total_count
    FROM JoinedData
)
SELECT *
FROM FinalWithCount
ORDER BY stat, rank;
