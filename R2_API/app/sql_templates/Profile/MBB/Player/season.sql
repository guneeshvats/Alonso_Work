SELECT * FROM {table_name}
    WHERE player_id = '{player_id}'
     AND period_number = '0'
            AND period_type = 'REGULAR'
        ORDER BY academic_season DESC;