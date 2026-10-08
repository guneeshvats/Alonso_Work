# Documentation for `mappings_handler.py`

# Technical Documentation for `MappingsHandler` Python Script

## Overview

The `MappingsHandler` script is designed to manage and retrieve various mappings from JSON configuration files. These mappings are used to configure database interactions, such as fetching table names, field mappings, filter criteria, and other metadata needed for constructing SQL queries or data manipulations. The mappings are stored in JSON files within a predefined directory structure, and the script provides a mechanism to preload and access these mappings efficiently.

## Dependencies

- **Python Standard Libraries**: The script utilizes standard libraries such as `os` for file path operations and `json` for parsing JSON files.
- **Custom Constants**: The script relies on constants defined in `MappingsHandlerTerms` from `app.constants` to standardize file and directory naming conventions.

## Class: `MappingsHandler`

### Purpose

The `MappingsHandler` class is responsible for loading and providing access to various mappings used in the application. These include table mappings, field mappings, filter mappings, position mappings, and other metadata, all stored in JSON format.

### Constructor: `__init__(self)`

- **Purpose**: Initializes the `MappingsHandler` instance and preloads mappings from JSON files to minimize file I/O operations during runtime.
- **Key Operations**:
  - Sets up directory paths based on the relative location of the script.
  - Preloads several mappings using the `_load_json` method to avoid repeated file access.

### Private Method: `_load_json(self, file_name: str) -> dict`

- **Purpose**: Loads a JSON file and returns its content as a dictionary.
- **Arguments**:
  - `file_name (str)`: Name of the JSON file to be loaded.
- **Returns**: Parsed JSON data as a dictionary.
- **Raises**: 
  - `RuntimeError` if the file is not found or if JSON parsing fails.
  
### Method: `get_table_name(self, sport_code: str, entity: str, stat_period: str) -> str`

- **Purpose**: Retrieves the table name based on sport code, entity type, and statistical period.
- **Arguments**:
  - `sport_code (str)`: Sport identifier (e.g., "MFB").
  - `entity (str)`: Entity type (e.g., "player", "team").
  - `stat_period (str)`: Statistical period (e.g., "game", "season").
- **Returns**: Corresponding table name or `None` if not found.

### Method: `get_fields_for_query(self, sport_code: str, entity: str, stat_period: str, query_type: str) -> list`

- **Purpose**: Fetches fields required for constructing SQL queries.
- **Arguments**:
  - `sport_code (str)`, `entity (str)`, `stat_period (str)`, `query_type (str)`.
- **Returns**: List of field names or an empty list if not found.

### Method: `load_filter_mappings(self) -> dict`

- **Purpose**: Provides access to preloaded filter mappings.
- **Returns**: Dictionary containing filter mappings.

### Method: `get_stat_mapping(self, sport_code: str, entity: str) -> dict`

- **Purpose**: Retrieves statistical mappings for a given sport and entity.
- **Arguments**:
  - `sport_code (str)`, `entity (str)`.
- **Returns**: Statistical mapping dictionary or an empty dictionary if the file is not found.

### Method: `get_query_samples(self, sport_code: str, entity: str) -> list`

- **Purpose**: Loads example queries for a given sport and entity.
- **Arguments**:
  - `sport_code (str)`, `entity (str)`.
- **Returns**: List of example queries or an empty list if the file is not found or if an error occurs.

### Method: `get_pos_mapping(self, sport_code: str) -> dict`

- **Purpose**: Retrieves position mappings for a specified sport.
- **Arguments**:
  - `sport_code (str)`.
- **Returns**: Position mapping dictionary.

### Method: `get_metadata_mapping(self) -> dict`

- **Purpose**: Returns metadata mappings.
- **Returns**: Dictionary containing metadata mappings.

## Important Implementation Details

- **Directory Structure**: The script assumes a specific directory structure relative to the script's location, particularly for the `data_config/mappings` directory.
- **JSON File Handling**: The script includes error handling for file not found and JSON parsing errors, raising `RuntimeError` where appropriate.
- **Preloading**: Mappings are preloaded during initialization to optimize performance by reducing the need for repeated file reads.
