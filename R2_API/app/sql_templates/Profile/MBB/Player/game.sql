 SELECT * FROM {table_name}
        WHERE player_id = '{player_id}'
            AND season = {season}
            AND period_number = '0'
            AND period_type = 'REGULAR'
                 ORDER BY season DESC;