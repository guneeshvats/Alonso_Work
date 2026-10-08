# Documentation for `search.py`

# Search API Module Documentation

This module provides API endpoints for searching and retrieving data from the R2 system. It supports both authenticated requests for detailed search functionality and public requests for name suggestions. The module is implemented using FastAPI and integrates several components, including natural language processing, SQL query generation, and database interactions.

## Overview

The module defines two primary endpoints:

1. **Search Endpoint** (`/search`): Allows authenticated users to execute complex search queries across sports data. It processes natural language queries, converts them into structured queries, and returns formatted results.
2. **Name Suggestions Endpoint** (`/name-suggestions`): Provides public access to auto-complete suggestions for player and team names based on a prefix.

## Dependencies

The module depends on several components and services:
- **FastAPI**: Framework used to define and handle HTTP requests.
- **Pydantic**: Used for data validation and serialization.
- **MongoDB**: Utilized for storing and querying team and player information.
- **PostgreSQL**: Utilized for executing complex SQL queries.
- **NLP Services**: Used for processing natural language queries into structured queries.
- **Logging**: Configured for tracking and debugging application behavior.

## Functions and Endpoints

### `get_pos_class_team_values`

```python
def get_pos_class_team_values(sport_code: str, qualifiers: dict) -> tuple:
```

This function dynamically fetches valid positions, player classes, and teams based on the provided sport code and qualifiers. It returns values for dropdown menus and filters in the UI, ensuring that options are relevant based on the existing qualifiers.

- **Args**:
  - `sport_code` (str): Sport identifier code (e.g., "MFB" for football, "MBB" for basketball).
  - `qualifiers` (dict): Dictionary of existing query qualifiers.
  
- **Returns**: A tuple containing available positions, player classes, and teams.

### `/search` Endpoint

```python
@router.post("/search", response_model=SearchResponse)
async def search_players(request: SearchRequest, username: str = Depends(verify_token)):
```

This is a protected endpoint for executing search queries across sports data. It processes natural language queries, converts them into AQL (Athlete Query Language), generates SQL, executes database queries, and returns the results. The endpoint supports pagination, sorting, and advanced filtering.

- **Args**:
  - `request` (SearchRequest): Contains search parameters such as query text, filters, and pagination.
  - `username` (str): Authenticated username from JWT token.
  
- **Returns**: `SearchResponse` containing search results, AQL and SQL queries, processing time, and available filter options.
  
- **Raises**:
  - `HTTPException`: For various error conditions with appropriate status codes.

### `/name-suggestions` Endpoint

```python
@public_router.post("/name-suggestions", response_model=NameSuggestionsResponse)
async def post_name_suggestions(request: NameSuggestionsRequest):
```

This public endpoint provides auto-complete suggestions for player and team names. It performs case-insensitive prefix matching against names and returns up to 10 matching suggestions.

- **Args**:
  - `request` (NameSuggestionsRequest): Contains sport code, entity type, and search prefix.

- **Returns**: `NameSuggestionsResponse` containing a list of matching name suggestions.

- **Raises**:
  - `HTTPException`: If no matches are found (404) or for server errors (500).

## Data Models

### `SearchRequest`

A Pydantic model for capturing search parameters, including query text, sport code, team code, and pagination details.

### `SearchResponse`

A Pydantic model for the response format of the search endpoint, including search results, generated queries, and processing metrics.

### `NameSuggestionsRequest`

A Pydantic model for capturing parameters for name suggestion requests, including sport code, entity type, and search prefix.

### `NameSuggestionsResponse`

A Pydantic model for the response format of the name suggestions endpoint, containing a list of suggestions.

## Logging

Logging is configured at the INFO level to track user actions, query processing steps, and error conditions. This facilitates debugging and auditing of search and suggestion operations.
