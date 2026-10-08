# Documentation for `sql_builder.py`

# Technical Documentation for SQLBuilder Script

## Overview

The `SQLBuilder` class is designed to dynamically convert AQL (Athlyte Query Language) queries into SQL queries. This is particularly useful in environments where AQL is used to define queries for sports-related data, and SQL is required to interact with databases such as PostgreSQL. The class leverages mappings and templates to construct complex SQL queries based on various parameters and query types.

## Detailed Explanation of Each Function

### `__init__(self)`

- **Purpose**: Initializes an instance of the `SQLBuilder` class.
- **Key Operations**:
  - Instantiates the `PGSQLAdapter`, `MappingsHandler`, and `SQLTemplateLoader` classes.
  - Loads stat mappings from a MongoDB collection via the `_load_stat_mapping` method.

### `_load_stat_mapping(self)`

- **Purpose**: Loads GeniusLabel to AthlyteShortLabel mappings from a MongoDB collection.
- **Return**: A dictionary mapping GeniusLabels to AthlyteShortLabels.
- **Error Handling**: Catches exceptions during database access and logs error messages.

### `convert_aql_to_sql(self, aql_output, sport_code, entity, filters, query_type, team_code, limit=10, offset=0, sort_by=None, sort_order=None)`

- **Purpose**: Converts an AQL query into an SQL query.
- **Parameters**:
  - `aql_output`: Parsed AQL query output.
  - `sport_code`: Code identifying the sport.
  - `entity`: Type of entity ('player' or 'team').
  - `filters`: Query filters to apply.
  - `query_type`: Type of query (e.g., 'BASIC', 'MIN').
  - `team_code`: Team identifier code.
  - `limit`: Number of results to return.
  - `offset`: Number of results to skip.
  - `sort_by`: Column to sort results by.
  - `sort_order`: Sort direction ('ASC' or 'DESC').
- **Returns**: A tuple containing the generated SQL query, count query, selected columns, and stat columns.
- **Exceptions**: Raises `ValueError` if no table mapping is found for the given parameters.

### `_get_selected_columns(self, sport_code, aql_output, entity, stat_period, query_type)`

- **Purpose**: Determines which columns should be selected based on the query type and conditions.
- **Returns**: A list of column names to select in the query.
- **Exceptions**: Raises `ValueError` if no field mappings are found.

### `_build_where_clause(self, conditions, qualifiers, filters, query_type)`

- **Purpose**: Constructs the SQL `WHERE` clause by combining conditions, qualifiers, and filters.
- **Returns**: A string representing the complete `WHERE` clause.
  
### `_format_filters(self, filters)`

- **Purpose**: Formats filter conditions for inclusion in the SQL `WHERE` clause.
- **Returns**: A list of formatted filter conditions.

### `_parse_query(self, query_type, table_name, selected_columns, where_clause, aql_output, limit, offset, sort_by, sort_order, entity, team_code, sport_code)`

- **Purpose**: A generic parser that handles various query types.
- **Returns**: A tuple with the generated SQL query, count query, selected columns, and stat columns.

### `_parse_basic_query`, `_parse_min_query`, `_parse_max_query`, `_parse_ltw_query`, `_parse_streak_query`

- **Purpose**: These functions each parse a specific type of query by delegating to the `_parse_query` method.
- **Returns**: A tuple with the results from the generic query parser.

### `_get_sort_mapping(self, query_type, stat_column)`

- **Purpose**: Determines the default sort column and order for different query types.
- **Returns**: A tuple containing the sort column and sort order.

### `_generate_query(self, query_type, table_name, selected_columns, where_clause, aql_output, limit, offset, sort_by, sort_order, entity, team_code, sport_code)`

- **Purpose**: Generates SQL queries from templates while avoiding duplicate `WHERE` clauses.
- **Returns**: A tuple containing the SQL query, count query, selected columns, and stat columns.
- **Exceptions**: Raises `ValueError` if a `MIN` or `MAX` query is missing a required stat field.

## Important Implementation Details

- **Dependencies**: 
  - `psycopg2` for PostgreSQL interactions.
  - `pymongo` for MongoDB interactions.
  - `decouple` for environment variable management.
  - Custom modules for mappings, database adapters, and SQL template loading.

- **Error Handling**: The script includes error handling for database operations, particularly within the `_load_stat_mapping` method.

- **Template Usage**: SQL queries are generated using templates loaded via the `SQLTemplateLoader`, allowing for dynamic query construction based on predefined patterns.

This documentation should provide a comprehensive understanding of the `SQLBuilder` class and its role in converting AQL queries into SQL queries.
