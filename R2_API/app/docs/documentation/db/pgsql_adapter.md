# Documentation for `pgsql_adapter.py`

## Technical Documentation for PGSQLAdapter Python Script

### Overview
The `PGSQLAdapter` script is designed to facilitate interaction between an application and a PostgreSQL database. It is specifically tailored for executing analytical queries, managing database connections, and transforming query results into a user-friendly format. By utilizing configuration mappings, the script enables the translation of database column names into more readable labels, thereby enhancing the interpretability of the data for end-users.

### Dependencies
This script relies on several external libraries and modules:
- `psycopg2`: A PostgreSQL database adapter for Python.
- `decouple`: Used to manage configuration and environment variables.
- `json`: For handling JSON data, particularly for reading mapping configurations.
- `logging`: To provide detailed logging for operations and errors.
- `os`: For interacting with the file system, particularly for path manipulations.
- `app.data_config.mappings.mappings_handler`: Custom module for managing metadata mappings.
- `app.constants`: Custom module defining constants for query types, qualifiers, sorting fields, and PostgreSQL environment variables.

### Detailed Explanation

#### Class: `PGSQLAdapter`
This class encapsulates the functionality required to interact with a PostgreSQL database, execute queries, and process results.

#### Initialization (`__init__` method)
- Establishes a connection to the PostgreSQL database using credentials and connection details sourced from environment variables.
- Initializes a cursor for executing database operations.
- Loads metadata mappings through the `MappingsHandler` to transform database column names into user-friendly labels.

#### Method: `close`
- Closes the database connection to ensure resource cleanup and connection pooling efficiency.

#### Method: `fetch_stat_mapping`
- **Purpose**: Retrieves mappings for statistical fields from JSON files specific to a sport and entity type (e.g., "Player" or "Team").
- **Args**:
  - `sport_code` (str): Identifier for the sport (e.g., "MFB" for football).
  - `entity` (str): Type of entity for which statistics are fetched.
- **Returns**: A dictionary mapping database column names to their corresponding display labels.
- **Implementation Details**:
  - Constructs the file path for the mapping file based on the sport code and entity.
  - Reads and parses JSON configuration to extract mappings.
  - Logs errors if the file is missing or cannot be parsed.

#### Method: `execute_query`
- **Purpose**: Executes SQL queries and formats the results using configured mappings.
- **Args**:
  - `sql_query` (str): The main SQL query to retrieve data.
  - `count_query` (str): A query to count the total number of records matching the criteria.
  - `selected_columns` (list): List of columns included in the metadata section of results.
  - `sport_code` (str): Sport identifier for mapping purposes.
  - `entity` (str): Entity type for statistical mapping.
  - `stat_columns` (list): Columns to be treated as statistical fields.
  - `aql_only` (bool, optional): If set to True, bypasses query execution returning empty results.
- **Returns**: A tuple containing:
  - `results`: A list of dictionaries with separate 'metadata' and 'stats' sections.
  - `total_count`: The count of matching records obtained from the count query.
- **Implementation Details**:
  - Executes the main SQL query and fetches results.
  - Maps database column names to user-friendly labels using sport-specific mappings.
  - Separates results into metadata and statistics based on provided column lists.
  - Executes the count query to determine the total number of records.

### Testing Section
Within the `__main__` block, a basic test scenario is executed:
- Constructs and executes a sample SQL query to retrieve player statistics.
- Prints the results and total count of records.
- Demonstrates the usage of the `PGSQLAdapter` class and its methods.
- Closes the database connection after test execution to ensure proper resource management.
