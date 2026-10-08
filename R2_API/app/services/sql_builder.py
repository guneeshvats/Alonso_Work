import json
import os
import sys
import psycopg2
import re
from pymongo import MongoClient
from decouple import config
from app.data_config.mappings.mappings_handler import MappingsHandler
from app.db.pgsql_adapter import PGSQLAdapter
from app.db.mongo_connection import db
from app.sql_templates.sql_template_loader import SQLTemplateLoader
from app.constants import QueryTypes, SortingFields, SortOrders, QUALIFIERS_MAPPING


class SQLBuilder:
    """
    Converts AQL (Athlyte Query Language) into SQL dynamically.
    """
    def __init__(self):
       # self.db_adapter = PGSQLAdapter()
        self.mappings_handler = MappingsHandler()
        self.sql_loader = SQLTemplateLoader()
        self.stat_mapping = self._load_stat_mapping()

    def _load_stat_mapping(self):
        """Fetches GeniusLabel → AthlyteShortLabel mapping from MongoDB."""
        try:
            collection = db['stat_mapping']
            return {
                entry['GeniusLabel'].lower(): entry['AthlyteShortLabel']
                for entry in collection.find()
            }
        except Exception as e:
            print(f"Error fetching stat mapping: {e}")
            return {}

    def convert_aql_to_sql(self, aql_output, sport_code, entity,filters, query_type, team_code, limit=10, offset=0, sort_by=None, sort_order=None):
        """
        Converts AQL (Athlyte Query Language) query to SQL based on query type.

        Args:
            aql_output (dict): The parsed AQL query output
            sport_code (str): Code identifying the sport (e.g. 'MFB', 'MBB')
            entity (str): Type of entity ('player' or 'team')
            filters (dict): Query filters to apply
            query_type (str): Type of query to execute
            team_code (str): Team identifier code
            limit (int, optional): Number of results to return. Defaults to 10
            offset (int, optional): Number of results to skip. Defaults to 0
            sort_by (str, optional): Column to sort results by. Defaults to None
            sort_order (str, optional): Sort direction ('ASC' or 'DESC'). Defaults to None

        Returns:
            tuple: Contains generated SQL query, count query, selected columns and stat columns

        Raises:
            ValueError: If no table mapping is found for the given parameters
        """
        stat_period = aql_output["stat_period"].lower()
        table_name = self.mappings_handler.get_table_name(sport_code, entity, stat_period)
        if not table_name:
            raise ValueError(f"No table mapping found for sport_code={sport_code}, entity={entity}, stat_period={stat_period}")
        
        selected_columns = self._get_selected_columns(sport_code ,aql_output, entity, stat_period, query_type)

        conditions = aql_output.get(SortingFields.CONDITIONS.value, "").strip()
        print("Conditions are:", conditions)
        qualifiers = aql_output.get(SortingFields.QUALIFIERS.value, {})
        where_clause = self._build_where_clause(conditions, qualifiers, filters, query_type)

        query_parsers = {
            QueryTypes.BASIC.value: self._parse_basic_query,
            QueryTypes.MIN.value: self._parse_min_query,
            QueryTypes.MAX.value: self._parse_max_query,
            QueryTypes.LTW.value: self._parse_ltw_query,
            QueryTypes.STREAK.value: self._parse_streak_query
        }
        
        if query_type.lower() not in query_parsers:
            raise ValueError(f"Query type '{query_type}' not implemented.")
        
        parser = query_parsers[query_type.lower()]
        return parser(table_name, selected_columns, where_clause, aql_output, limit, offset, sort_by, sort_order, entity, team_code, sport_code)

    def _get_selected_columns(self, sport_code, aql_output, entity, stat_period, query_type):
        """
        Determines which columns should be selected based on query type and conditions.

        Args:
            sport_code (str): Code identifying the sport
            aql_output (dict): The parsed AQL query output
            entity (str): Type of entity (player/team)
            stat_period (str): Statistical period (game/season)
            query_type (str): Type of query being executed

        Returns:
            list: Column names to select in the query

        Raises:
            ValueError: If no field mappings are found for the given parameters
        """
        selected_columns = self.mappings_handler.get_fields_for_query(sport_code, entity, stat_period, query_type)
        if not selected_columns:
            raise ValueError(f"No field mappings found for entity={entity}, stat_period={stat_period}, query_type={query_type}")


        sel_col_pat = re.compile("\s+AND|and|OR|or\s+")
        col_extr_pat = re.compile("s_[a-z0-9_]+")
        
        conditions = aql_output.get(SortingFields.CONDITIONS.value, "").strip()
        stat_columns = {
            col_extr_pat.findall(stat)[0]
            for stat in sel_col_pat.split(conditions)
            if col_extr_pat.findall(stat) != []
        }
        print(f"Stat Columns: {stat_columns}")
        return list(set(selected_columns) | stat_columns)

    def _build_where_clause(self, conditions, qualifiers, filters, query_type):
        """
        Builds SQL WHERE clause by combining conditions, qualifiers and filters.

        Args:
            conditions (str): Raw conditions from AQL query
            qualifiers (dict): Query qualifiers to apply
            filters (dict): Additional filters to apply
            query_type (str): Type of query being executed

        Returns:
            str: Complete WHERE clause for SQL query
        """
        where_conditions = set()

        if conditions:
            if any(op in conditions for op in [">", "<", "=", "!=", ">=", "<="]):
                where_conditions.add(f"({conditions.strip()})")
            elif query_type not in [QueryTypes.MIN.value, QueryTypes.MAX.value]:
                if not conditions.endswith("IS NOT NULL"):
                    where_conditions.add(f"({conditions.strip()} IS NOT NULL)")
                else:
                    where_conditions.add(f"({conditions.strip()})")

        for key, value in qualifiers.items():
            key = QUALIFIERS_MAPPING.get(key, key)
            if isinstance(value, list):
                formatted_value = "', '".join(value)
                where_conditions.add(f"{key} IN ('{formatted_value}')")
            else:
                where_conditions.add(f"{key} = '{value}'")

        filter_conditions = self._format_filters(filters)
        print(f"Filters: {filter_conditions}")
        where_conditions.update(filter_conditions)

        period_conditions = []
        ## Change this in R2: Check if the period is a quarter"
        period_conditions += ["period_type = 'REGULAR'", "period_number='0'"]
        where_conditions.update(period_conditions)

        # value_conditions = [""]

        return " AND ".join(where_conditions) if where_conditions else ""

    def _format_filters(self, filters):
        """
        Formats filter conditions for SQL WHERE clause.

        Args:
            filters (dict): Dictionary of filters to format

        Returns:
            list: Formatted filter conditions ready for SQL
        """
        filter_conditions = []
        filter_mappings = self.mappings_handler.load_filter_mappings()
        for key, value in filters.items():
            if key in filter_mappings:
                column_name, operator = filter_mappings[key]
                formatted_value = "', '".join(value) if isinstance(value, list) else value
                filter_conditions.append(f"{column_name} {operator} ('{formatted_value}')" if operator == "IN" else f"{column_name} {operator} '{formatted_value}'")
        return filter_conditions

    def _parse_query(self, query_type, table_name, selected_columns, where_clause, aql_output, limit, offset, sort_by, sort_order, entity, team_code, sport_code):
        """
        Generic query parser that handles all query types.
        
        Args:
            query_type (str): Type of query (basic, min, max, ltw, streak)
            table_name (str): Name of the database table
            selected_columns (list): Columns to select
            where_clause (str): WHERE clause conditions
            aql_output (dict): Output from AQL parsing
            limit (int): Number of results to return
            offset (int): Number of results to skip
            sort_by (str): Column to sort by
            sort_order (str): Sort order (ASC/DESC)
            entity (str): Entity type (player/team)
            team_code (str): Team identifier code
            sport_code (str): Sport identifier code
            
        Returns:
            tuple: Generated SQL query, count query, selected columns and stat columns
        """
        return self._generate_query(query_type, table_name, selected_columns, where_clause, aql_output, limit, offset, sort_by, sort_order, entity, team_code, sport_code)

    def _parse_basic_query(self, *args, **kwargs):
        """
        Parses a basic query by delegating to the generic parser.
        
        Args:
            *args: Variable length argument list passed to generic parser
            **kwargs: Arbitrary keyword arguments passed to generic parser
            
        Returns:
            tuple: Results from generic query parser for basic query type
        """
        return self._parse_query(QueryTypes.BASIC.value, *args, **kwargs)

    def _parse_min_query(self, *args, **kwargs):
        """
        Parses a minimum value query by delegating to the generic parser.
        
        Args:
            *args: Variable length argument list passed to generic parser
            **kwargs: Arbitrary keyword arguments passed to generic parser
            
        Returns:
            tuple: Results from generic query parser for minimum query type
        """
        return self._parse_query(QueryTypes.MIN.value, *args, **kwargs)

    def _parse_max_query(self, *args, **kwargs):
        """
        Parses a maximum value query by delegating to the generic parser.
        
        Args:
            *args: Variable length argument list passed to generic parser
            **kwargs: Arbitrary keyword arguments passed to generic parser
            
        Returns:
            tuple: Results from generic query parser for maximum query type
        """
        return self._parse_query(QueryTypes.MAX.value, *args, **kwargs)

    def _parse_ltw_query(self, *args, **kwargs):
        """
        Parses a last time when query by delegating to the generic parser.
        
        Args:
            *args: Variable length argument list passed to generic parser
            **kwargs: Arbitrary keyword arguments passed to generic parser
            
        Returns:
            tuple: Results from generic query parser for LTW query type
        """
        return self._parse_query(QueryTypes.LTW.value, *args, **kwargs)

    def _parse_streak_query(self, *args, **kwargs):
        """
        Parses a streak query by delegating to the generic parser.
        
        Args:
            *args: Variable length argument list passed to generic parser
            **kwargs: Arbitrary keyword arguments passed to generic parser
            
        Returns:
            tuple: Results from generic query parser for streak query type
        """
        return self._parse_query(QueryTypes.STREAK.value, *args, **kwargs)

    def _get_sort_mapping(self, query_type, stat_column):
        """
        Gets the default sort column and order for different query types.

        Args:
            query_type (str): Type of query being executed
            stat_column (str): Statistical column being queried

        Returns:
            tuple: Contains sort column and sort order (ASC/DESC)
        """
        if query_type == QueryTypes.LTW.value:
            stat_period = getattr(self, "stat_period_for_ltw", "").lower()
            if stat_period == "season":
                return (SortingFields.SEASON.value, SortOrders.DESC.value)
            else:
                return (SortingFields.GAMEDATE.value, SortOrders.DESC.value)

        # Default Sorting orders for different query types
        sort_mapping = {
            QueryTypes.BASIC.value: (stat_column, SortOrders.DESC.value),
            QueryTypes.MIN.value: (stat_column, SortOrders.ASC.value),
            QueryTypes.MAX.value: (stat_column, SortOrders.DESC.value),
            QueryTypes.STREAK.value: (SortingFields.STREAKLENGTH.value, SortOrders.DESC.value)
        }
        
        return sort_mapping.get(query_type, (stat_column, SortOrders.ASC.value))

    def _generate_query(self, query_type, table_name, selected_columns, where_clause, aql_output, limit, offset, sort_by, sort_order, entity, team_code, sport_code):
        """
        Generate SQL queries from templates while avoiding duplicate WHERE clauses.

        Args:
            query_type (str): Type of query (basic, min, max, ltw, streak)
            table_name (str): Name of the database table
            selected_columns (list): Columns to select
            where_clause (str): WHERE clause conditions
            aql_output (dict): Output from AQL parsing
            limit (int): Number of results to return
            offset (int): Number of results to skip
            sort_by (str): Column to sort by
            sort_order (str): Sort order (ASC/DESC)
            entity (str): Entity type (player/team)
            team_code (str): Team identifier code
            sport_code (str): Sport identifier code

        Returns:
            tuple: Contains:
                - str: Generated SQL query
                - str: Count query
                - list: Selected columns
                - list: Stat columns used in query

        Raises:
            ValueError: If min/max query is missing required stat field
        """

        print("Sorting Info", sort_by, sort_order)
        template_key = (f"{query_type}_{sport_code.lower()}_{entity.lower()}" 
                       if query_type == QueryTypes.STREAK.value 
                       else query_type)
        
        sql_template = self.sql_loader.load_template(template_key)

        formatted_team_code = f"'{team_code}'" if sport_code == "MBB" else team_code

        conditions = aql_output.get(SortingFields.CONDITIONS.value, "").strip()
        streak_length = aql_output.get("streak_len", "")

        if streak_length == None:
            streak_length = "1"

        print(f"Streak Length is {streak_length}")

        pat = re.compile("\s+AND|and|OR|or\s+")
        col_extr_pat = re.compile("s_[a-z0-9_]+")

        stat_columns = col_extr_pat.findall(conditions) if conditions else set()
        print(f"New stat cols: {stat_columns}")
        if query_type in [QueryTypes.MIN.value, QueryTypes.MAX.value]:
            if not stat_columns:
                raise ValueError(f"{query_type.upper()} query must have a valid stat field.")
            stat_column = list(stat_columns)[0]
        else:
            stat_column = next(iter(stat_columns), None)

        self.stat_period_for_ltw = aql_output.get("stat_period", "").lower()
        default_sort_by, default_sort_order = self._get_sort_mapping(query_type, stat_column)



        final_sort_by = sort_by or default_sort_by
        final_sort_order = default_sort_order
        if sort_order:
            final_sort_order = sort_order.upper()

        print("Sorting Info", final_sort_by, final_sort_order)

        # final_sort_order = (sort_order.upper()
        #                    if sort_order and sort_order.upper() in [SortOrders.ASC, SortOrders.DESC]
        #                    else default_sort_order)

        if query_type != QueryTypes.STREAK.value:
            stat_column_conditions = [f"{stat_column} != 0" for stat_column in stat_columns]
            where_clause = where_clause + " AND " +" AND ".join(stat_column_conditions)


        formatted_where_clause = (f"AND {where_clause}" 
                                if query_type in [QueryTypes.MIN.value, QueryTypes.MAX.value] and where_clause 
                                else f"WHERE {where_clause}" if where_clause else "")

        sql_query = sql_template.format(
            table_name=table_name,
            selected_columns=", ".join(selected_columns),
            stat_column=stat_column or "",
            where_clause=formatted_where_clause.strip(),
            conditions=conditions,
            streak_length=streak_length,
            final_sort_by=final_sort_by,
            final_sort_order=final_sort_order,
            limit=limit,
            offset=offset,
            team_code=formatted_team_code
        )

        count_query = f"SELECT COUNT(*) FROM {table_name}"
        if where_clause:
            count_query += f" WHERE {where_clause}"
        count_query += ";"

        return sql_query, count_query, selected_columns, list(stat_columns)

