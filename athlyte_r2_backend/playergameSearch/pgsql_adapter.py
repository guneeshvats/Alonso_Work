import psycopg2
from decouple import config
from psycopg2 import sql
import json
from decimal import Decimal
import re
import os
from datetime import date

# Mapping of entity and stat_period to corresponding PostgreSQL tables


class PGSQLAdapter:
    """PostgreSQL Adapter to convert AQL to SQL and execute queries."""

    def __init__(self):
        """Initialize connection to PostgreSQL."""
        self.conn = psycopg2.connect(
            dbname="athlyte_ftbl",
            user="athlyte",
            password="%Um8pE@4QUJAwF9K",
            host="3.145.61.23",
            port="5432"
        )
        self.cursor = self.conn.cursor()

        # Table mapping based on available tables
        self.PG_TABLES = {
            # ("player", "career"): "player_career_statistics",
            # ("player", "season"): "player_season_statistics",
            ("player", "game"): "player_game_statistics",
            ("player", "season"): "player_season_statistics_mfb_pilot",
            ("player", "career"): "player_career_statistics_mfb_pilot",
        }

        self.metadata_mapping = {
            "id": "ID",
            "season": "SEASON",
            "playerclass": "CLASS",
            "teamname": "TEAM",
            "gameresult": "RES",
            "opponentteamname": "OPP",
            "gamedate": "DATE",
            "playername": "PLAYER",
            "position": "POS",
            "streak_len": "STREAK LENGTH",
            "start_game_date": "START DATE",
            "end_game_date": "END DATE",
            "start_opponent": "START OPP",
            "end_opponent": "END OPP"
        }

        self.reverse_metadata_mapping = {y : x for x, y in self.metadata_mapping.items()}
        self.reverse_metadata_mapping["playerName"] = "playername"

    def format_filters(self, filters):
        # TODO : Remove Hard Coding !
        #  Prepare Dynamic Filter Conditions
        filter_conditions = {}
        if 'RES' in filters:
            filter_conditions['gameResult'] = f"gameresult IN {tuple(filters['RES'])}"

        if 'PLAYER' in filters:
            player_names = "', '".join(filters['PLAYER'])  # Convert list to SQL string
            filter_conditions["playerName"] = f"playername IN ('{player_names}')"

        if 'CLASS' in filters:
            player_classes = "', '".join(filters['CLASS'])
            filter_conditions["playerClass"] = f"playerclass IN ('{player_classes}')"

        if 'OPP' in filters:
            opponent_names = "', '".join(filters['OPP'])
            filter_conditions["opponentTeamName"] = f"opponentteamname IN ('{opponent_names}')"

        if 'DATE_MIN' in filters:
            if "gameDate" not in filter_conditions:
                filter_conditions["gameDate"] = []
            filter_conditions["gameDate"].append(f"gamedate >= '{filters['DATE_MIN']}'")

        if 'DATE_MAX' in filters:
            filter_conditions["gameDate"].append(f"gamedate <= '{filters['DATE_MAX']}'")

        if 'POS' in filters:
            positions = "', '".join(filters['POS'])
            filter_conditions["position"] = f"position IN ('{positions}')"

        return filter_conditions


    def parse_basic(self, aql, team_code=None, count_only=False, skip=0, limit=20, filters={}, sort_by=None, sort_order="asc"):
        """
        Convert AQL (Athlyte Query Language) into a SQL query with filters and sorting.

        Args:
            aql (dict): AQL query containing conditions, entity, and stat_period.
            count_only (bool): If True, returns only the count of rows.
            skip (int): Number of rows to skip (pagination).
            limit (int): Number of rows to fetch (pagination).
            sort_by (str): Column to sort by.
            sort_order (str): Sorting order ("asc" or "desc").
        
        Returns:
            str: SQL query string.
        """

        qualifiers = aql.get("qualifier", {})  #  Extract Qualifiers

        # print(f"AQL : {aql}")
        conditions = aql.get("conditions", "").strip()
        stat_period = aql.get("stat_period", "").lower()
        entity = aql.get("entity", "").lower()

        filter_conditions = self.format_filters(filters)

        if not entity or not stat_period:
            raise ValueError("Missing 'entity' or 'stat_period' in AQL.")

        source_table = self.PG_TABLES.get((entity, stat_period))
        if not source_table:
            raise ValueError(f"No mapping found for entity '{entity}' and stat_period '{stat_period}'.")

        # Extract column names from the conditions string
        relevant_columns = self.extract_relevant_fields(conditions, source_table)

        # Ensure primary fields are included

        always_include = ["playername",  "teamname", "position"] # Remove Hard Coding !
        if stat_period == "season":
            always_include += ["playerclass", "season"]
        if stat_period == "game":
            always_include += ["season", "playerclass", "opponentteamname", "gameresult", "gamedate"]

        selected_columns = ", ".join(set(relevant_columns).union(always_include))

        sql_conditions = conditions.replace('"', "")  # Remove double quotes


        #  Add Qualifiers First
        qualifier_conditions = []
        for key, value in qualifiers.items():
            if isinstance(value, list):  
                formatted_value = "', '".join(value)
                qualifier_conditions.append(f"{key} IN ('{formatted_value}')")
            else:
                qualifier_conditions.append(f"{key} = '{value}'")

                        #  Merge Qualifiers into SQL Conditions
        if qualifier_conditions:
            sql_conditions = " AND ".join(qualifier_conditions) if not sql_conditions else sql_conditions + " AND " + " AND ".join(qualifier_conditions)


        # Add team_code condition if provided
        # team_code cannot be given by qualifiers - change this
        if team_code and ('teamName' not in qualifiers):
            team_condition = f"teamcode = '{team_code}'"  # Assuming team_code is a string
            if sql_conditions:
                sql_conditions += f" AND {team_condition}"
            else:
                sql_conditions = team_condition

                #  Add Filters **ONLY IF** the same key is NOT present in Qualifiers
        selected_filter_conditions = []
        small_case_qualifier_keys = [x.lower() for x, y in qualifiers.items()]
        for filter_name, filter_item in filter_conditions.items():
            # temp_filter_item = filter_item.replace("IN", "=").replace(">=", "=").replace("<=", "=").replace(">", "=").replace("<", "=")
            # filter_key = temp_filter_item.split(" = ")[0].strip()  # Extract column name
            if filter_name.lower() not in small_case_qualifier_keys:
                if type(filter_item) == str:
                    selected_filter_conditions.append(filter_item)
                else:
                    for fitem in filter_item:
                        selected_filter_conditions.append(fitem)

        if selected_filter_conditions:
            sql_conditions += f" AND {' AND '.join(selected_filter_conditions)}" if sql_conditions else " AND ".join(selected_filter_conditions)

        where_clause = f"WHERE {sql_conditions}" if sql_conditions else ""

        #  Ensure sorting is valid
        valid_sort_columns = ["playername", "playerclass", "season", "opponentteamname", "gamedate", "gameresult", "teamname", "position"]

        print("Basic SortBy", sort_by, sort_order, type(sort_by))
        if not sort_by:
            sort_by = relevant_columns[0]  # Sort by first relevant stat column
        else:
            sort_by = self.reverse_metadata_mapping[sort_by]

        sort_by = sort_by.lower()
        sort_order = sort_order.upper() if sort_order.lower() in ["asc", "desc"] else "ASC"


        order_clause = f"ORDER BY {sort_by} {sort_order}"

        count_query = f"SELECT COUNT(*) FROM {source_table} {where_clause};"

        if count_only:
            query = f"SELECT COUNT(*) FROM {source_table} {where_clause};"
        else:
            query = f"""
            SELECT ROW_NUMBER() OVER () AS id, {selected_columns} 
            FROM {source_table} {where_clause} 
            {order_clause}  
            LIMIT {limit} OFFSET {skip};
            """

        return query, count_query, selected_columns
    

    def parse_min_query(self, aql, team_code=None, count_only=False, skip=0, limit=20, filters=None, sort_by=None, sort_order="asc"):
        """
        Convert AQL into SQL query to find the minimum value while applying filters, sorting, and qualifiers.
        """
        stat_period = aql.get("stat_period", "").lower()
        entity = aql.get("entity", "").lower()
        conditions = aql.get("conditions", "").strip()
        qualifiers = aql.get("qualifier", {})

        if not entity or not stat_period:
            raise ValueError("Missing 'entity' or 'stat_period' in AQL.")

        source_table = self.PG_TABLES.get((entity, stat_period))
        if not source_table:
            raise ValueError(f"No mapping found for entity '{entity}' and stat_period '{stat_period}'.")

        #  Extract stat field for MIN query
        match = re.search(r"(s\w+)", conditions)
        if not match:
            raise ValueError("No valid stat field found for min query.")

        stat_field = match.group(1)

        #  Apply Qualifiers (Priority)
        sql_conditions_list = []
        for key, value in qualifiers.items():
            if isinstance(value, list):  
                formatted_value = "', '".join(value)
                sql_conditions_list.append(f"{key} IN ('{formatted_value}')")
            else:
                sql_conditions_list.append(f"{key} = '{value}'")

        # Add team_code condition if provided
        # team_code cannot be given by qualifiers - change this
        if team_code and ('teamName' not in qualifiers):
            team_condition = f"teamcode = '{team_code}'"  # Assuming team_code is a string
            if sql_conditions_list:
                sql_conditions_list.append(f"{team_condition}")
            else:
                sql_conditions_list = [team_condition]

       # elif (qualifiers['teamName'] == 'any')

        #  Apply Filters (If Not Overwritten by Qualifiers)
        filter_conditions = self.format_filters(filters)
        small_case_qualifier_keys = [x.lower() for x in qualifiers.keys()]
        for filter_name, filter_value in filter_conditions.items():
            if filter_name.lower() not in small_case_qualifier_keys:
                if isinstance(filter_value, list):
                    formatted_value = "', '".join(filter_value)
                    sql_conditions_list.append(f"{filter_name} IN ('{formatted_value}')")
                else:
                    sql_conditions_list.append(f"{filter_name} = '{filter_value}'")

        #  Ensure conditions are correctly formatted
        if conditions and conditions != stat_field:  # Avoid invalid "AND stat_field"
            sql_conditions_list.append(conditions)

        #  Build WHERE Clause
        where_clause = "AND "+ f" {' AND '.join(sql_conditions_list)}" if sql_conditions_list else ""
        where_clause = f"WHERE {conditions} IS NOT NULL {where_clause}"


        #  Sorting - Ensure Sorting is Valid
        valid_sort_columns = ["playername", "playerclass", "season", "opponentteamname", "gamedate", "gameresult", "teamname", "position"]

        print("Min SortBy", sort_by, sort_order, type(sort_by))

        if sort_by is None:
            sort_by = stat_field  # Sort by first relevant stat column
        else:
            sort_by = self.reverse_metadata_mapping[sort_by]

        sort_by = sort_by.lower()
        sort_order = sort_order.upper() if sort_order.lower() in ["asc", "desc"] else "ASC"


        # order_clause = f"ORDER BY {sort_by} {sort_order}"
        order_clause = f"ORDER BY {sort_by} ASC"


        # Extract relevant columns dynamically based on conditions
        relevant_columns = [conditions]

        # Ensure primary fields are always included
        always_include = ["playername", "teamname", "position"]  # Remove Hard Coding !
        if stat_period == "season":
            always_include += ["playerclass", "season"]
        if stat_period == "game":
            always_include += ["season", "playerclass", "opponentteamname", "gameresult", "gamedate"]

        selected_columns = ", ".join(set(relevant_columns).union(always_include))  # Convert to a comma-separated string

        if count_only:
            query = f"SELECT COUNT(*) FROM {source_table} {where_clause};"
        else:
            query = f"""
            SELECT ROW_NUMBER() OVER () AS id, {selected_columns} 
            FROM {source_table} 
            {where_clause}
            {order_clause}
            LIMIT {limit} OFFSET {skip};
            """
        
        count_query = f"SELECT COUNT(*) FROM {source_table} {where_clause};"

        return query, count_query, selected_columns




    def parse_max_query(self, aql, team_code=None, count_only=False, skip=0, limit=20, filters=None, sort_by=None, sort_order="asc"):
        """
        Convert AQL into SQL query to find the maximum value while applying filters, sorting, and qualifiers.
        """
        stat_period = aql.get("stat_period", "").lower()
        entity = aql.get("entity", "").lower()
        conditions = aql.get("conditions", "").strip()
        qualifiers = aql.get("qualifier", {})

        if not entity or not stat_period:
            raise ValueError("Missing 'entity' or 'stat_period' in AQL.")

        source_table = self.PG_TABLES.get((entity, stat_period))
        if not source_table:
            raise ValueError(f"No mapping found for entity '{entity}' and stat_period '{stat_period}'.")

        #  Extract stat field for MAX query
        match = re.search(r"(s\w+)", conditions)
        if not match:
            raise ValueError("No valid stat field found for max query.")

        stat_field = match.group(1)

        #  Apply Qualifiers (Priority)
        sql_conditions_list = []
        for key, value in qualifiers.items():
            if isinstance(value, list):  
                formatted_value = "', '".join(value)
                sql_conditions_list.append(f"{key} IN ('{formatted_value}')")
            else:
                sql_conditions_list.append(f"{key} = '{value}'")

                # Add team_code condition if provided
                # team_code cannot be given by qualifiers - change this
        if team_code and ('teamName' not in qualifiers):
            team_condition = f"teamcode = '{team_code}'"  # Assuming team_code is a string
            if sql_conditions_list:
               sql_conditions_list.append(f"{team_condition}")
            else:
                sql_conditions_list = [team_condition]

        #  Apply Filters (If Not Overwritten by Qualifiers)
        filter_conditions = self.format_filters(filters)
        small_case_qualifier_keys = [x.lower() for x in qualifiers.keys()]
        for filter_name, filter_value in filter_conditions.items():
            if filter_name.lower() not in small_case_qualifier_keys:
                if isinstance(filter_value, list):
                    formatted_value = "', '".join(filter_value)
                    sql_conditions_list.append(f"{filter_name} IN ('{formatted_value}')")
                else:
                    sql_conditions_list.append(f"{filter_name} = '{filter_value}'")

        #  Ensure conditions are correctly formatted
        if conditions and conditions != stat_field:  # Avoid invalid "AND stat_field"
            sql_conditions_list.append(conditions)


        #  Build WHERE Clause
        where_clause = "AND " + f"{' AND '.join(sql_conditions_list)}" if sql_conditions_list else ""
        where_clause = f"WHERE {conditions} IS NOT NULL {where_clause} "
        #  Sorting - Ensure Sorting is Valid
        valid_sort_columns = ["playername", "playerclass", "season", "opponentteamname", "gamedate", "gameresult", "teamname", "position"]

        if not sort_by:
            sort_by = stat_field  # Sort by first relevant stat column
        else:
            sort_by = self.reverse_metadata_mapping[sort_by]

        sort_by = sort_by.lower()
        sort_order = sort_order.upper() if sort_order.lower() in ["asc", "desc"] else "ASC"


        # order_clause = f"ORDER BY {sort_by} {sort_order}"
        order_clause = f"ORDER BY {sort_by} DESC"

        #  Extract relevant columns dynamically
        # Extract relevant columns dynamically based on conditions
        #relevant_columns = self.extract_relevant_fields(conditions, source_table)
        relevant_columns = [conditions]
        # Ensure primary fields are always included
        always_include = ["playername", "teamname", "position"]  # Remove Hard Coding !
        if stat_period == "season":
            always_include += ["playerclass", "season"]
        if stat_period == "game":
            always_include += ["season", "playerclass", "opponentteamname", "gameresult", "gamedate"]

        selected_columns = ", ".join(set(relevant_columns).union(always_include))  # Convert to a comma-separated string

        if count_only:
            query = f"SELECT COUNT(*) FROM {source_table} {where_clause};"
        else:
            query = f"""
            SELECT ROW_NUMBER() OVER () AS id, {selected_columns} 
            FROM {source_table} 
            {where_clause}
            {order_clause}
            LIMIT {limit} OFFSET {skip};
            """


        count_query = f"SELECT COUNT(*) FROM {source_table} {where_clause};"

        return query, count_query, selected_columns
    


    def parse_ltw_query(self, aql, team_code=None, count_only=False, skip=0, limit=20, filters=None, sort_by=None, sort_order="asc"):
        """
        Convert AQL into SQL query to find the last occurrence when a condition was met.

        Args:
            aql (dict): AQL query containing conditions, entity, and stat_period.
            team_code (str): Team code for filtering.
            count_only (bool): If True, returns only the count of rows.
            skip (int): Number of rows to skip (pagination).
            limit (int): Number of rows to fetch (pagination).
            filters (dict): Filters from request.

        Returns:
            tuple: (sql_query, count_query, selected_columns)
        """

        stat_period = aql.get("stat_period", "").lower()
        entity = aql.get("entity", "").lower()
        conditions = aql.get("conditions", "").strip()
        qualifiers = aql.get("qualifier", {})

        if not entity or not stat_period:
            raise ValueError("Missing 'entity' or 'stat_period' in AQL.")

        source_table = self.PG_TABLES.get((entity, stat_period))
        if not source_table:
            raise ValueError(f"No mapping found for entity '{entity}' and stat_period '{stat_period}'.")

        #  Apply Qualifiers (Priority)
        sql_conditions_list = []
        for key, value in qualifiers.items():
            if isinstance(value, list):  
                formatted_value = "', '".join(value)
                sql_conditions_list.append(f"{key} IN ('{formatted_value}')")
            else:
                sql_conditions_list.append(f"{key} = '{value}'")

        # Apply team_code filter if not in qualifiers
        if team_code and ('teamName' not in qualifiers):
            sql_conditions_list.append(f"teamcode = '{team_code}'")

        #  Apply Filters (If Not Overwritten by Qualifiers)
        filter_conditions = self.format_filters(filters)
        small_case_qualifier_keys = [x.lower() for x in qualifiers.keys()]
        for filter_name, filter_value in filter_conditions.items():
            if filter_name.lower() not in small_case_qualifier_keys:
                if isinstance(filter_value, list):
                    formatted_value = "', '".join(filter_value)
                    sql_conditions_list.append(f"{filter_name} IN ('{formatted_value}')")
                else:
                    sql_conditions_list.append(f"{filter_name} = '{filter_value}'")

        #  Ensure conditions are correctly formatted
        if conditions:
            sql_conditions_list.append(conditions)

        #  Build WHERE Clause
        where_clause = f"WHERE {' AND '.join(sql_conditions_list)}" if sql_conditions_list else ""

        # **Sort by `gamedate` in DESCENDING ORDER**

        if not sort_by:
            sort_by = "gamedate" # Sort by first relevant stat column
        else:
            sort_by = self.reverse_metadata_mapping[sort_by]

        order_clause = f"ORDER BY {sort_by} DESC"

        # Extract relevant columns dynamically
        relevant_columns = self.extract_relevant_fields(conditions, source_table)

        # Ensure primary fields are always included
        always_include = ["playername", "teamname", "position"]
        if stat_period == "season":
            always_include += ["playerclass", "season"]
        if stat_period == "game":
            always_include += ["season", "playerclass", "opponentteamname", "gameresult", "gamedate"]

        selected_columns = ", ".join(set(relevant_columns).union(always_include))

        if count_only:
            query = f"SELECT COUNT(*) FROM {source_table} {where_clause};"
        else:
            query = f"""
            SELECT ROW_NUMBER() OVER () AS id, {selected_columns} 
            FROM {source_table} 
            {where_clause}
            {order_clause}
            LIMIT {limit} OFFSET {skip};
            """

        count_query = f"SELECT COUNT(*) FROM {source_table} {where_clause};"

        return query, count_query, selected_columns


    # def parse_streak_query(self, aql, team_code=None, count_only=False, skip=0, limit=20, filters=None, sort_by="gamedate", sort_order="ASC"):
    #     """
    #     Converts AQL into SQL to find streaks of games meeting certain conditions.

    #     Args:
    #         aql (dict): AQL query containing conditions, entity, and stat_period.
    #         team_code (str): Team code for filtering.
    #         count_only (bool): If True, returns only the count of rows.
    #         skip (int): Number of rows to skip (pagination).
    #         limit (int): Number of rows to fetch (pagination).
    #         filters (dict): Filters from request.
    #         sort_by (str): Column to sort by.
    #         sort_order (str): Sorting order ("ASC" or "DESC").

    #     Returns:
    #         tuple: (sql_query, count_query, selected_columns)
    #     """
    #     stat_period = aql.get("stat_period", "").lower()
    #     entity = aql.get("entity", "").lower()
    #     conditions = aql.get("conditions", "").strip()
    #     qualifiers = aql.get("qualifier", {})
    #     streak_len = aql.get("streak_len", None)  # Extracted but not used

    #     if not entity or not stat_period:
    #         raise ValueError("Missing 'entity' or 'stat_period' in AQL.")

    #     source_table = self.PG_TABLES.get((entity, stat_period))
    #     if not source_table:
    #         raise ValueError(f"No mapping found for entity '{entity}' and stat_period '{stat_period}'.")

    #     # Define ordering
    #     order_clause = f"ORDER BY {sort_by} {sort_order}"

    #     # Extract relevant columns dynamically
    #     relevant_columns = self.extract_relevant_fields(conditions, source_table)
    #     always_include = ["playername", "teamname", "position"]
    #     if stat_period == "season":
    #         always_include += ["playerclass", "season"]
    #     if stat_period == "game":
    #         always_include += ["season", "playerclass", "opponentteamname", "gameresult", "gamedate"]

    #     stat_columns = ", ".join(set(relevant_columns).union(always_include))

    #     # Load the SQL template from the file
    #     sql_template_path = os.path.join(os.path.dirname(__file__), "streak_computation.sql")
    #     with open(sql_template_path, "r") as file:
    #         sql_template = file.read()

    #     # Replace placeholders with actual values
    #     sql_query = sql_template.format(
    #         stat_columns=stat_columns,
    #         conditions=conditions,
    #         table_name=source_table,
    #         team_code=team_code or '',
    #         limit=limit,
    #         skip=skip
    #     ) + f" {order_clause};"  # Append sorting clause

    #     # count_query = f"SELECT COUNT(*) FROM ({sql_query}) AS subquery;"
    #     count_query = f"SELECT COUNT(*) FROM ({sql_query.rsplit('LIMIT', 1)[0]}) AS subquery;"

    #     return sql_query, count_query, stat_columns


    def parse_streak_query(self, aql, team_code=None, count_only=False, skip=0, limit=20, filters=None, sort_by=None, sort_order="DESC"):
        """
        Converts AQL into SQL to find streaks of games meeting certain conditions.

        Args:
            aql (dict): AQL query containing conditions, entity, and stat_period.
            team_code (str): Team code for filtering.
            count_only (bool): If True, returns only the count of rows.
            skip (int): Number of rows to skip (pagination).
            limit (int): Number of rows to fetch (pagination).
            filters (dict): Filters from request.
        Returns:
            tuple: (sql_query, count_query, selected_columns)
        """
        stat_period = aql.get("stat_period", "").lower()
        entity = aql.get("entity", "").lower()
        conditions = aql.get("conditions", "").strip()
        qualifiers = aql.get("qualifier", {})
        streak_len = aql.get("streak_len", None)

        if not entity or not stat_period:
            raise ValueError("Missing 'entity' or 'stat_period' in AQL.")

        source_table = self.PG_TABLES.get((entity, stat_period))
        if not source_table:
            raise ValueError(f"No mapping found for entity '{entity}' and stat_period '{stat_period}'.")

        order_clause = f"ORDER BY {sort_by} {sort_order}"

        # Extract relevant columns dynamically
        relevant_columns = self.extract_relevant_fields(conditions, source_table)
        always_include = ["playername", "teamname", "season", "streak_len", "start_game_date", "end_game_date", "start_opponent", "end_opponent"]

        stat_columns = ", ".join(set(relevant_columns).union(always_include))
        relevant_columns = ", ".join(set(relevant_columns))

        if not sort_by:
            sort_by = "streak_length"  # Sort by first relevant stat column
        else:
            sort_by = self.reverse_metadata_mapping[sort_by]
        # **Updated SQL Query**
        sql_query = f"""
        WITH AllGames AS (
            SELECT
                playerId,
                playername,
                season,
                TO_DATE(gamedate, 'YYYY-MM-DD') AS gamedate,
                {relevant_columns},
                opponentteamname,
                teamcode,
                teamname,
                opponentteamcode,
                CASE WHEN {conditions} THEN 1 ELSE 0 END AS meets_criteria
            FROM {source_table}
            WHERE periodnumber = 0
            AND teamCode = {team_code}
        ),
        RankedGames AS (
            SELECT
                playerId,
                playername,
                season,
                gamedate,
                {relevant_columns},
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
        SELECT ROW_NUMBER() OVER () AS id, playername, teamname, season, streak_length, start_game_date, start_opponent, end_game_date, end_opponent
        FROM FinalStreaks
        WHERE streak_length > 1
        ORDER BY {sort_by} DESC
        LIMIT {limit} OFFSET {skip};


        """

        print(sql_query)

        # count_query = f"SELECT COUNT(*) FROM ({sql_query}) AS subquery;"
        count_query = f"SELECT COUNT(*) FROM ({sql_query.rsplit('LIMIT', 1)[0]}) AS subquery;"


        return sql_query, count_query, stat_columns




    def extract_relevant_fields(self, conditions, table):
        """
        Extracts column names from the AQL conditions string.

        Args:
            conditions (str): The conditions string from AQL.
            table (str): The name of the database table.

        Returns:
            list: A list of extracted column names.
        """
        # Use regex to extract words before comparison operators (=, >, <, >=, <=, !=)
        matches = re.findall(r"([\w]+)\s*(?:=|>|<|>=|<=|!=)", conditions)

        # Remove duplicates and ensure valid column names
        return list(set(matches))
    

    def execute_query(self, sql_query, selected_columns, stat_mapping_ad):
        """
        Execute a SQL query on the PostgreSQL database.

        Args:
            sql_query (str): The SQL query string.
            selected_columns (list): Columns that should be placed in the "stats" section.

        Returns:
            tuple: (column_names, query_results)
        """
        print(f"selected_columns: {selected_columns}")
        try:
            print(sql_query)
            self.cursor.execute(sql_query)
            rows = self.cursor.fetchall()
            column_names = [desc[0] for desc in self.cursor.description]

            #  Define Metadata Mapping


            results = []
            for row in rows:
                row_dict = {
                    column_names[i]: (
                        int(value) if column_names[i] == "season" and isinstance(value, Decimal) else 
                        float(value) if isinstance(value, Decimal) else value
                    ) for i, value in enumerate(row) if value not in ["", None]
                }

                #  Apply Metadata Mapping
                metadata = {"ID": row_dict["id"]}  # Ensure "ID" is always included
                for k, v in row_dict.items():
                    print("MD", k, v)
                    if k in selected_columns and k != "id":
                        mapped_key = self.metadata_mapping.get(k, k)  # Use mapped label if exists, otherwise original key
                        if isinstance(v, date):
                            v = v.isoformat()
                        metadata[mapped_key] = v  # Add mapped metadata key-value pair

                #  Apply Stats Mapping (with Uppercase Conversion)
                stats = {}
                for k, v in row_dict.items():
                    print("Stat", k, v)
                    if k not in selected_columns and k != "id":
                        mapped_key = stat_mapping_ad.get(k, None)  # Direct lookup
                        if not mapped_key:
                            mapped_key = stat_mapping_ad.get(k.capitalize(), None)  # Try capitalized
                        if not mapped_key:
                            mapped_key = stat_mapping_ad.get(k.lower(), None)  # Try lowercase
                        if not mapped_key:
                            mapped_key = k  # If all fails, keep original

                        mapped_key = mapped_key.upper()  #  Convert to uppercase
                        stats[mapped_key] = v

                results.append({
                    "metadata": metadata,
                    "stats": stats
                })

            return column_names, results
        except Exception as e:
            print(f"Database error: {e}")
            return [], []


    def close_connection(self):
        """Close the database connection."""
        self.cursor.close()
        self.conn.close()



if __name__ == "__main__":
    adapter = PGSQLAdapter()

    # Sample AQL input
    aql_input = {
        "entity": "player",
        "query": "players with 143+ career pat pass made and 92+ career quarterback hurries",
        "aql": {
            "query_type": "basic",
            "entity": "player",
            "qualifiers": {},
            "stat_period": "career",
            "conditions": 'sPatPasses >= 143 AND sPassQuarterbackHurries >= 92'
        }
    }

    # Generate SQL
    sql_query = adapter.parse_basic(aql_input["aql"])
    print("Generated SQL Query:\n", sql_query)

    # Close connection
    adapter.close_connection()


if __name__ == "__main__":
    adapter = PGSQLAdapter()

    # Sample AQL input
    aql_input = {
        "entity": "player",
        "query": "players with 143+ career pat pass made and 92+ career quarterback hurries",
        "aql": {
            "query_type": "basic",
            "entity": "player",
            "qualifiers": {},
            "stat_period": "career",
            "conditions": 'sPatPasses >= 143 AND sPassQuarterbackHurries >= 92'
        }
    }

    # Generate SQL
    sql_query = adapter.parse_basic(aql_input["aql"])
    print("Generated SQL Query:\n", sql_query)

    # Close connection
    adapter.close_connection()