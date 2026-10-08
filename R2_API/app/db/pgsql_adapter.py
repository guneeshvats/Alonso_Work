import psycopg2
from decouple import config
import json
from decimal import Decimal
import os
from datetime import date
from collections import defaultdict
import logging
from app.data_config.mappings.mappings_handler import MappingsHandler
from app.constants import QueryTypes, Qualifiers, SortingFields, SortOrders, PostgreSQL
from app.sql_templates.sql_template_loader import SQLTemplateLoader
import time

# Configure logging with standard format including timestamp and log level
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


class PGSQLAdapter:
    """
    PostgreSQL Adapter for executing analytical queries and transforming results.
    
    This adapter serves as a bridge between the application's query interface and PostgreSQL database.
    It handles database connections, query execution, and result transformation using configurable
    mappings for statistics and metadata fields.
    
    Key responsibilities:
    - Manages PostgreSQL database connection
    - Executes SQL queries and retrieves results
    - Transforms database column names to user-friendly labels
    - Handles error cases and provides detailed logging
    - Maintains separation between statistical and metadata fields
    """

    def __init__(self, pg_pool):
        """
        Initializes database connection and loads required mapping configurations.
        
        Establishes PostgreSQL connection using environment variables defined in PostgreSQL enum.
        Loads metadata mappings used for transforming column names in query results.
        
        Environment variables required:
        - PG_DB: Database name
        - PG_USER: Database username
        - PG_PASSWORD: Database password  
        - PG_HOST: Database host
        - PG_PORT: Database port
        """
        # self.conn = psycopg2.connect(
        #     dbname=config(PostgreSQL.PG_DB.value),
        #     user=config(PostgreSQL.PG_USER.value),
        #     password=config(PostgreSQL.PG_PASSWORD.value),
        #     host=config(PostgreSQL.PG_HOST.value),
        #     port=config(PostgreSQL.PG_PORT.value),
        # )
        self.pg_pool = pg_pool
        self.conn = self.pg_pool.getconn()
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()
        logger.info("PostgreSQL Connection Established.")

        # Load Mappings 
        self.mappings_handler = MappingsHandler()
        self.metadata_mapping = self.mappings_handler.get_metadata_mapping()

    def close(self):
        """Closes the PostgreSQL database connection."""
        #self.conn.close()
        self.pg_pool.putconn(self.conn)

    def get_stat_mapping_by_position(self, sport_code, entity, player_position):
        stat_mapping = self.fetch_stat_mapping_R2(sport_code, entity)
        return stat_mapping.get(player_position, stat_mapping.get("ALL", {}))


    def fetch_stat_mapping(self, sport_code, entity):
        """
        Retrieves statistical field mappings from JSON configuration files.
        
        Loads sport and entity specific mapping configurations that define how database column names
        should be transformed into user-friendly labels in the query results.
        
        Args:
            sport_code (str): Sport identifier code (e.g. "MFB" for football)
            entity (str): Type of entity ("Player" or "Team") for which stats are being fetched
            
        Returns:
            dict: Mapping of database column names to their display labels
                 Empty dict if mapping file is not found or contains errors
                 
        Example mapping:
            {"rushing_yards": "RUSH_YDS", "passing_yards": "PASS_YDS"}
        """
        base_dir = os.path.abspath(os.path.dirname(__file__))
        stat_mapping_path = os.path.join(base_dir, "..", "data_config", "mappings", "stat_mapping", sport_code,
                                         f"{entity}.json")
        stat_mapping_path = os.path.normpath(stat_mapping_path)

        if not os.path.exists(stat_mapping_path):
            logger.error(f"Stat mapping file not found: {stat_mapping_path}")
            return {}

        try:
            if not os.path.exists(stat_mapping_path):
                logger.error(f"Stat mapping file not found: {stat_mapping_path}")
                raise FileNotFoundError(f"File not found: {stat_mapping_path}")

            with open(stat_mapping_path, "r", encoding="utf-8") as file:
                stat_data = json.load(file)
            return {entry["stat"].lower(): entry["short_label"] for entry in stat_data if "short_label" in entry}
        except Exception as e:
            logger.error(f"Error loading stat mapping from file {stat_mapping_path}: {e}")
            return {}

    def fetch_stat_to_short_name(self, sport_code, entity):
        """
        Retrieves statistical field mappings from JSON configuration files.

        Loads sport and entity specific mapping configurations that define how database column names
        should be transformed into user-friendly labels in the query results.

        Args:
            sport_code (str): Sport identifier code (e.g. "MFB" for football)
            entity (str): Type of entity ("Player" or "Team") for which stats are being fetched

        Returns:
            dict: Mapping of database column names to their display labels
                 Empty dict if mapping file is not found or contains errors

        Example mapping:
               {"sFieldGoalAttemptLongest": "FGA Long","sFieldGoalsMade": "FGM",}
        """
        base_dir = os.path.abspath(os.path.dirname(__file__))
        stat_mapping_path = os.path.join(base_dir, "..", "data_config", "mappings", "stat_mapping", sport_code,
                                         "stats_to_shortname", f"{entity}.json")
        stat_mapping_path = os.path.normpath(stat_mapping_path)

        if not os.path.exists(stat_mapping_path):
            logger.error(f"Stat mapping file not found: {stat_mapping_path}")
            return {}

        try:
            if not os.path.exists(stat_mapping_path):
                logger.error(f"Stat mapping file not found: {stat_mapping_path}")
                raise FileNotFoundError(f"File not found: {stat_mapping_path}")

            with open(stat_mapping_path, "r", encoding="utf-8") as file:
                stat_data = json.load(file)
            return stat_data
        except Exception as e:
            logger.error(f"Error loading stat mapping from file {stat_mapping_path}: {e}")
            return {}
    def fetch_stat_mapping_R2(self, sport_code, entity):
        """
        Retrieves statistical field mappings from JSON configuration files.
        
        Loads sport and entity specific mapping configurations that define how database column names
        should be transformed into user-friendly labels in the query results.
        
        Args:
            sport_code (str): Sport identifier code (e.g. "MFB" for football)
            entity (str): Type of entity ("Player" or "Team") for which stats are being fetched
            
        Returns:
            dict: Mapping of database column names to their display labels
                 Empty dict if mapping file is not found or contains errors
                 
        Example mapping:
            {"rushing_yards": "RUSH_YDS", "passing_yards": "PASS_YDS"}
        """
        base_dir = os.path.abspath(os.path.dirname(__file__))
        stat_mapping_path = os.path.join(base_dir, "..", "data_config", "mappings", "stat_mapping", sport_code, "category_to_stats", f"{entity}.json")
        stat_mapping_path = os.path.normpath(stat_mapping_path)

        if not os.path.exists(stat_mapping_path):
            logger.error(f"Stat mapping file not found: {stat_mapping_path}")
            return {}

        try:
            if not os.path.exists(stat_mapping_path):
                logger.error(f"Stat mapping file not found: {stat_mapping_path}")
                raise FileNotFoundError(f"File not found: {stat_mapping_path}")

            with open(stat_mapping_path, "r", encoding="utf-8") as file:
                stat_data = json.load(file)
            return stat_data
        except Exception as e:
            logger.error(f"Error loading stat mapping from file {stat_mapping_path}: {e}")
            return {}
        
    def fetch_streaks_mapping(self, sport_code, entity):
        """
        Retrieves statistical field mappings from JSON configuration files.

        Loads sport and entity specific mapping configurations that define how database column names
        should be transformed into user-friendly labels in the query results.

        Args:
            sport_code (str): Sport identifier code (e.g. "MFB" for football)
            entity (str): Type of entity ("Player" or "Team") for which stats are being fetched

        """
        base_dir = os.path.abspath(os.path.dirname(__file__))
        stat_mapping_path = os.path.join(base_dir, "..", "data_config", "mappings", "stat_mapping", sport_code, "streaks_mapping", f"{entity}.json")
        stat_mapping_path = os.path.normpath(stat_mapping_path)

        if not os.path.exists(stat_mapping_path):
            logger.error(f"Stat mapping file not found: {stat_mapping_path}")
            return {}

        try:
            if not os.path.exists(stat_mapping_path):
                logger.error(f"Stat mapping file not found: {stat_mapping_path}")
                raise FileNotFoundError(f"File not found: {stat_mapping_path}")

            with open(stat_mapping_path, "r", encoding="utf-8") as file:
                stat_data = json.load(file)
            return stat_data
        except Exception as e:
            logger.error(f"Error loading stat mapping from file {stat_mapping_path}: {e}")
            return {}


    def execute_query(self, sql_query, count_query, selected_columns, sport_code, entity, stat_columns, aql_only=False):
        """
        Executes SQL query and formats results using configured mappings.
        
        This method handles the complete query execution workflow:
        1. Executes the main SQL query to fetch results
        2. Maps database columns to appropriate display labels using sport-specific mappings
        3. Separates results into metadata and statistical components
        4. Executes count query to get total number of matching records
        
        Args:
            sql_query (str): Main SQL query to execute
            count_query (str): SQL query to get total count of results
            selected_columns (list): List of columns to include in metadata section
            sport_code (str): Sport identifier code for loading correct mappings
            entity (str): Entity type ('Player' or 'Team') for stat mapping
            stat_columns (list): List of columns to be treated as statistics
            aql_only (bool, optional): If True, returns empty results without executing query
            
        Returns:
            tuple: (results, total_count) where:
                  - results: List of dicts with 'metadata' and 'stats' sections
                  - total_count: Total number of records matching query criteria
                  
        Example return:
            ([{
                'metadata': {'ID': 123, 'PLAYER': 'John Doe'},
                'stats': {'RUSH_YDS': 100, 'TDS': 2}
            }], 1)
        """
        if aql_only:
            logger.info("Skipping SQL execution, returning only AQL output.")
            return [], 0

        try:
            logger.info("Executing SQL Query:\n" + sql_query)
            s = time.time()
            self.cursor.execute(sql_query)
            e = time.time()

            rows = self.cursor.fetchall()

            print(f"Query execution took {e-s} seconds")


            column_names = [desc[0].lower() for desc in self.cursor.description]
            stat_mapping = self.fetch_stat_mapping(sport_code, entity)

            results = []
            total_count = 0


            for row_num, row in enumerate(rows):
                row_dict = {column_names[i]: value for i, value in enumerate(row)}

                if row_num == 0:
                    total_count = row_dict.get("total_count", 0)

                metadata = {"ID": row_dict.get("id", None)}
                stats = {}
                for key, value in row_dict.items():
                    key_lower = key.lower()

                    if key_lower == "total_count":
                        continue

                    if key_lower in stat_mapping:
                        mapped_key = stat_mapping[key_lower]
                        stats[mapped_key] = value
                    else:
                        mapped_key = self.metadata_mapping.get(key_lower, key_lower).upper()
                        metadata[mapped_key.upper()] = value

                stats = {}
                for key in stat_columns:
                    key_lower = key.lower()
                    if key_lower in row_dict:
                        mapped_key = stat_mapping.get(key_lower, None)
                        if mapped_key:
                            stats[mapped_key.upper()] = row_dict[key_lower]

                results.append({"metadata": metadata, "stats": stats})

            #self.cursor.execute(count_query)
            #total_count = self.cursor.fetchone()[0]

            return results, total_count

        except Exception as e:
            logger.error(f"Database Query Error: {e}")
            return [], 0

    def execute_player_profile(self, sport_code, player_id, entity="Player", stat_period="season"):
        """
        Executes a SQL query for player profile.
        
        Args:
            sport_code (str): Sport code ('MFB' or 'MBB').
            entity (str): Entity type ('Player' or 'Team').
            player_id (str): Player identifier code.
        
        Returns:
            dict: Player profile data.
        """
        try:

            table_name = self.mappings_handler.get_table_name(sport_code, entity, stat_period)
            query = SQLTemplateLoader(f'app/sql_templates/Profile/{sport_code}/{entity}').load_template(
                f"{stat_period}")
            query = query.format(player_id=player_id, table_name=table_name)
            logger.info(f"Executing SQL Query:\n{query}")

            self.cursor.execute(query)
            rows = self.cursor.fetchall()

            if not rows:
                return None

            stat_to_short_name = self.fetch_stat_to_short_name(sport_code, entity)
            stat_to_short_name = defaultdict(lambda: None, stat_to_short_name)
            column_names = [stat_to_short_name[desc[0]] or desc[0] for desc in self.cursor.description]

            player_data = [dict(zip(column_names, row)) for row in rows]

            first_record = player_data[0]
            player_name = first_record.get("player_name", "")
            team_name = first_record.get("team_name", "")
            team_code = first_record.get("team_code", "")
            player_position = first_record.get("position", "")

            stat_mapping = self.fetch_stat_mapping_R2(sport_code, entity)
            # stat_mapping = stat_mapping[player_position]
            stat_mapping = self.get_stat_mapping_by_position(sport_code, entity, player_position)


            stats_names = [stat for sublist in stat_mapping.values() for stat in sublist]

            stats_names.append("season")

            filtered_player_data = []
            for record in player_data:
                filtered_record = {k: v for k, v in record.items() if k in stats_names}
                filtered_player_data.append(filtered_record)


            return {
                "PlayerName": player_name,
                "SportCode": sport_code,
                "TeamName": team_name,
                "TeamCode": str(team_code),
                "PlayerPosition": player_position,
                "stats": filtered_player_data,
                "stat_mapping": stat_mapping
            }

        except Exception as e:
            logger.error(f"Database Query Error: {e}")
            raise
        finally:
            self.cursor.close()

    def execute_player_game_logs(self, sport_code, player_id, season=None, entity="Player", stat_period="game"):
        """
        Executes a SQL query for player profile.

        Args:
            sport_code (str): Sport code ('MFB' or 'MBB').
            entity (str): Entity type ('Player' or 'Team').
            player_id (str): Player identifier code.

        Returns:
            dict: Player profile data.
        """
        try:

            table_name = self.mappings_handler.get_table_name(sport_code, entity, stat_period)
            sql_query_seasons = f"""
                SELECT DISTINCT season
                FROM {table_name}
                WHERE player_id = '{player_id}'
                ORDER BY season DESC;
            """
            self.cursor.execute(sql_query_seasons)
            seasons = self.cursor.fetchall()
            seasons = [season[0] for season in seasons]
            if season:
                pass
            else:
                season = seasons[0]

            query = SQLTemplateLoader(f'app/sql_templates/Profile/{sport_code}/{entity}').load_template(
                f"{stat_period}")
            logger.info(f"Executing SQL Query:\n{query}")

            self.cursor.execute(query.format(player_id=player_id, season=f"'{season}'", table_name=table_name))
            rows = self.cursor.fetchall()
            # print(rows)

            if not rows:
                return None

            stat_mapping = self.fetch_stat_mapping_R2(sport_code, entity)
            stat_to_short_name = self.fetch_stat_to_short_name(sport_code, entity)
            stat_to_short_name = defaultdict(lambda: None, stat_to_short_name)
            column_names = [stat_to_short_name[desc[0]] or desc[0] for desc in self.cursor.description]
            player_data = [dict(zip(column_names, row)) for row in rows]
            # print(player_data)

            first_record = player_data[0]
            player_name = first_record.get("player_name", "")
            team_name = first_record.get("team_name", "")
            team_code = first_record.get("team_code", "")
            player_position = first_record.get("position", "")
            # stat_mapping = stat_mapping[player_position]
            stat_mapping = self.get_stat_mapping_by_position(sport_code, entity, player_position)


            stats_names = [stat for sublist in stat_mapping.values() for stat in sublist]
            stats_names.append("season")
            stats_names.append("opponent_team_name")
            stats_names.append("game_date")

            filtered_player_data = []
            for record in player_data:
                filtered_record = {k: v for k, v in record.items() if k in stats_names}
                filtered_player_data.append(filtered_record)

            return {
                "PlayerName": player_name,
                "SportCode": sport_code,
                "TeamName": team_name,
                "TeamCode": str(team_code),
                "PlayerPosition": player_position,
                "Seasons": seasons,
                "stats": filtered_player_data,
                "stat_mapping": stat_mapping
            }

        except Exception as e:
            logger.error(f"Database Query Error: {e}")
            raise
        finally:
            self.cursor.close()

    # def execute_player_records(self, sport_code, entity, player_id, teamcode, stat_period, rank_threshold):
    #     try:

    #         team_code_sql = f"""
    #             SELECT team_code FROM pgs_interim_mfb_pilot WHERE player_id = '{player_id}' LIMIT 1
    #         """

    #        # print(team_code_sql)

    #         self.cursor.execute(team_code_sql)
    #         team_codes = self.cursor.fetchall()
    #         teamcode = team_codes[0][0]


    #         query = SQLTemplateLoader(f'app/sql_templates/Records/{sport_code}/{entity}').load_template(stat_period)
    #         print(f"Team Code is {teamcode}")
    #         query = query.format(player_id=player_id, team_code=f"{teamcode}", rank_threshold=rank_threshold,)

    #         print(f"Executing SQL Query:\n{query}")
    #         self.cursor.execute(query)
    #         rows = self.cursor.fetchall()
    #         stat_to_short_name = self.fetch_stat_to_short_name(sport_code, entity)
    #         # print(rows)
    #         column_names = [desc[0] for desc in self.cursor.description]
    #         player_records = [dict(zip(column_names, row)) for row in rows]
    #         total_count = player_records[0]['total_count'] if player_records else 0

    #         for i in range(len(player_records)):
    #             player_records[i]['stat'] = stat_to_short_name.get(player_records[i]['stat'].lower(),
    #                                                                player_records[i]['stat'])

    #         return {"PlayerRecords": player_records, "TotalCount": total_count}
    #     except Exception as e:
    #         logger.error(f"Database Query Error: {e}")
    #         raise
    #     finally:
    #         self.cursor.close()
    def execute_player_records(self, sport_code, entity, player_id, teamcode, stat_period, rank_threshold):
        """
        Executes a SQL query to retrieve player records and their rankings.

        This function fetches player records from the database based on the provided parameters.
        It first validates and retrieves the correct team code for the player, then executes
        a template-based SQL query to get the player's records and their rankings within
        their team. The results are transformed to include short names for statistics.

        Args:
            sport_code (str): The code representing the sport (e.g., 'MBB', 'MFB')
            entity (str): The type of entity (e.g., 'Player', 'Team')
            player_id (str): The unique identifier for the player
            teamcode (str): The team code (will be validated/overridden if incorrect)
            stat_period (str): The period for which stats are being retrieved (e.g., 'season', 'career')
            rank_threshold (int): The maximum rank to include in results

        Returns:
            dict: A dictionary containing:
                - PlayerRecords (list): List of dictionaries containing player records with stats and rankings
                - TotalCount (int): Total number of records found

        Raises:
            ValueError: If no team code is found for the given player_id
            Exception: For any database query errors or other unexpected errors
        """
        try:
            # Get the correct table name based on sport code
            table_name = self.mappings_handler.get_table_name(sport_code, entity, stat_period)

            # Safely fetch team code (in case input is blank or wrong)
            team_code_sql = f"""
                SELECT team_code FROM {table_name} WHERE player_id = '{player_id}' LIMIT 1
            """
            self.cursor.execute(team_code_sql)
            team_codes = self.cursor.fetchall()
            if not team_codes:
                raise ValueError(f"No team_code found for player_id = {player_id}")
            teamcode = team_codes[0][0]

            # Load the SQL template for the correct sport/entity/stat_period
            query = SQLTemplateLoader(f'app/sql_templates/Records/{sport_code}/{entity}').load_template(stat_period)
            logger.info(f"Team Code is {teamcode}")
            query = query.format(player_id=player_id, team_code=f"{teamcode}", rank_threshold=rank_threshold)
            logger.info(f"Executing SQL Query:\n{query}")

            self.cursor.execute(query)
            rows = self.cursor.fetchall()

            stat_to_short_name = self.fetch_stat_to_short_name(sport_code, entity)
            column_names = [desc[0] for desc in self.cursor.description]
            player_records = [dict(zip(column_names, row)) for row in rows]
            total_count = player_records[0]['total_count'] if player_records else 0

            for i in range(len(player_records)):
                player_records[i]['stat'] = stat_to_short_name.get(player_records[i]['stat'].lower(),
                                                                player_records[i]['stat'])

            return {"PlayerRecords": player_records, "TotalCount": total_count}
        except Exception as e:
            logger.error(f"Database Query Error: {e}")
            raise
        finally:
            self.cursor.close()


    def execute_player_highs(self, sport_code, entity, player_id, stat_period):
        try:
            self.cursor = self.conn.cursor()
            query = SQLTemplateLoader(f'app/sql_templates/Highs/{sport_code}/{entity}').load_template(
                f"{stat_period}_high")
            query = query.format(player_id=player_id)

            logger.info(f"Executing SQL Query:\n{query}")

            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            column_names = [desc[0].lower() for desc in self.cursor.description]
            player_highs = [dict(zip(column_names, row)) for row in rows]
            total_count = player_highs[0]['total_count'] if player_highs else 0
            stat_to_short_name = self.fetch_stat_to_short_name(sport_code, entity)

            for i in range(len(player_highs)):
                player_highs[i]['stat'] = stat_to_short_name.get(player_highs[i]['stat'].lower(),
                                                                 player_highs[i]['stat'])

            return {"PlayerHighs": player_highs, "TotalCount": total_count}
        except Exception as e:
            logger.error(f"Database Query Error: {e}")
            raise
        finally:
            self.cursor.close()

    def get_player_streaks(self, sport_code, entity, player_id, teamcode, stat, stat_value, streak_length):
        try:
            query = SQLTemplateLoader(f'app/sql_templates/Streaks/{sport_code}/{entity}').load_template(f"streaks")
            query = query.format(player_id=f"'{player_id}'", team_code=f"'{teamcode}'", stat=f"{stat.lower()}",
                                 stat_value=stat_value, streak_length=streak_length)
            logger.info(f"Executing SQL Query:\n{query}")

            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            if not rows:
                return {"PlayerStreaks": [], "TotalCount": 0}
            column_names = [desc[0].lower() for desc in self.cursor.description]
            player_streaks = [dict(zip(column_names, row)) for row in rows]

            return {"PlayerStreaks": player_streaks, "TotalCount": player_streaks[0]['total_count']}
        except Exception as e:
            logger.error(f"Database Query Error: {e}")
            raise
        finally:
            self.cursor.close()


# === Testing PGSQLAdapter for Basic Queries ===
from psycopg2 import pool
from decouple import config
from app.constants import PostgreSQL

# === Testing PGSQLAdapter for Basic Queries ===
if __name__ == "__main__":
    # Set up the PostgreSQL connection pool
    pg_pool = pool.SimpleConnectionPool(
        minconn=1,
        maxconn=5,
        database=config(PostgreSQL.PG_DB.value),
        user=config(PostgreSQL.PG_USER.value),
        password=config(PostgreSQL.PG_PASSWORD.value),
        host=config(PostgreSQL.PG_HOST.value),
        port=config(PostgreSQL.PG_PORT.value),
    )

    adapter = PGSQLAdapter(pg_pool)

    # Test Query for "basic"
    test_sql = """
    SELECT playername, teamname, position, gamedate, opponentteamname, gameresult, rushing_yards, touchdowns
    FROM player_game_statistics 
    WHERE rushing_yards > 50 AND teamname = 'Alabama' AND season = '2022' 
    ORDER BY playername DESC 
    LIMIT 10 OFFSET 0;
    """

    test_count_sql = """
    SELECT COUNT(*) 
    FROM player_game_statistics 
    WHERE rushing_yards > 50 AND teamname = 'Alabama' AND season = '2022';
    """

    # Example selected columns (should match actual columns in query)
    test_columns = ["playername", "teamname", "position", "gamedate", "opponentteamname", "gameresult", "rushing_yards", "touchdowns"]

    # Run the test
    results, count = adapter.execute_query(test_sql, test_count_sql, test_columns, sport_code="MFB", entity="Player", stat_columns=["rushing_yards", "touchdowns"])
    
    print("\n=== Query Results ===")
    print(results)
    print(f"\nTotal Count: {count}")

    # Close the DB connection
    adapter.close()
