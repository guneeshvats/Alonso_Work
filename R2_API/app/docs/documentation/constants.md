# Documentation for `constants.py`

# Technical Documentation for Enum-Based Configuration Script

## Overview
This Python script defines a series of enumerations (`Enum` classes) that encapsulate various constants and configurations used in a sports-related database application. The enumerations categorize and define constants for query qualifiers, sorting fields, database tables, user authentication fields, mapping configurations, and other components crucial for managing and querying sports statistics data. These enums provide structured and readable representations of constant values used throughout the application, promoting maintainability and type safety.

## Enumerations and Their Roles

### 1. `Qualifiers`
- **Purpose**: Defines constants for filtering queries based on player, team, and game attributes.
- **Fields Include**:
  - `PLAYER_NAME`: Filter by player name.
  - `PLAYER_CLASS`: Filter by player class.
  - `TEAM_NAME`: Filter by team name.
  - `TEAM_CONFERENCE_NAME`: Filter by team conference name.
  - `OPPONENT_TEAM_NAME`: Filter by opponent team name.
  - `POSITION`: Filter by player position.
  - `OPPONENT_CONFERENCE_NAME`: Filter by opponent conference name.
  - `SEASON`: Filter by season.
  - `IS_HOME_GAME`: Filter by home game status.
  - `TEAM_CODE`: Filter by team code.

### 2. `SortingFields`
- **Purpose**: Provides constants for sorting query results based on various criteria.
- **Fields Include**:
  - `PLAYER_NAME`: Sort by player name.
  - `TEAM_NAME`: Sort by team name.
  - `SEASON`: Sort by season.
  - `POSITION`: Sort by position.
  - Other fields include conditions, qualifiers, game date, streak length, player class, opponent team name, and query type.

### 3. `DatabaseTables`
- **Purpose**: Defines the canonical database table names for storing player and team statistics.
- **Fields Include**:
  - `PLAYER_STATS`: Table for player game statistics.
  - `TEAM_STATS`: Table for team game statistics.

### 4. `SortOrders`
- **Purpose**: Specifies the sorting order for query results.
- **Fields Include**:
  - `ASC`: Ascending order.
  - `DESC`: Descending order.

### 5. `QueryTypes`
- **Purpose**: Enumerates different types of statistical queries that can be executed.
- **Fields Include**:
  - `BASIC`: Standard statistical queries.
  - `MIN`: Minimum value queries.
  - `MAX`: Maximum value queries.
  - `LTW`: Last time when queries.
  - `STREAK`: Streak analysis queries.

### 6. `PlayerClass`
- **Purpose**: Represents valid NCAA player classification years.
- **Fields Include**:
  - `FRESHMAN`, `JUNIOR`, `SENIOR`, `SOPHOMORE`: Standard academic classifications.

### 7. `Positions`
- **Purpose**: Lists valid player positions across supported sports like football and men's basketball.
- **Fields Include**:
  - Football positions such as `CB`, `QB`, `WR`, etc.
  - Men's Basketball positions such as `C`, `F`, `G`.

### 8. `UserDataAuthentication`
- **Purpose**: Specifies fields related to user authentication and session management.
- **Fields Include**:
  - `EMAIL`, `TEAM`, `SPORTS`, `USERNAME`, `ISACTIVE`, `HASHEDPWD`, `USERID`, `ACCESSTOKEN`, `REFRESHTOKEN`, `TOKENTYPE`, `BEARER`.

### 9. `MappingsHandlerTerms`
- **Purpose**: Defines standard file names and paths for mapping configurations.
- **Fields Include**:
  - Files like `TABLE_MAPPING`, `FIELDS_MAPPING`, `FILTER_MAPPINGS`, etc.

### 10. `General`
- **Purpose**: Contains general constants used across the application.
- **Fields Include**:
  - `STAT`, `DESCRIPTION`, `STAT_PERIOD`.

### 11. `LLMModels`
- **Purpose**: Enumerates supported Language Learning Models and associated APIs.
- **Fields Include**:
  - Models like `GPT4`, `GEMINI_FLASH`, and API keys for `OPENAI`, `GEMINI`, etc.

### 12. `PostgreSQL`
- **Purpose**: Defines environment variables required for PostgreSQL database configuration.
- **Fields Include**:
  - `PG_DB`, `PG_USER`, `PG_PASSWORD`, `PG_HOST`, `PG_PORT`.

## Implementation Details
- The script uses Python's `enum` module to create typed enumerations, which improves code readability and reduces errors by restricting values to predefined constants.
- Each enumeration provides a clear and organized way to manage configuration constants, ensuring that the application components are consistent and maintainable.

## Dependencies
- Python's standard library module `enum` is required for defining enumerations. No additional third-party dependencies are necessary for this script.

This documentation provides a thorough understanding of the purpose and usage of each enumeration within the script, aiding developers in maintaining and extending the database application's functionality.
