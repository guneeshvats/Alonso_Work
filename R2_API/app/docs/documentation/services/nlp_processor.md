# Documentation for `nlp_processor.py`

# Python Script Documentation

## Overview

This Python script defines a class, `NlpProcessor`, that converts natural language queries into structured Analytics Query Language (AQL) commands. It leverages a Language Model (LLM) and a version control system called Folio for prompt management. The script integrates with various dependencies to fetch context, manage mappings, and ensure accurate query conversion and validation.

## Class and Methods

### Class: `NlpProcessor`

The `NlpProcessor` class is responsible for processing natural language queries, converting them into AQL format, and ensuring the queries are contextually accurate based on team and sport-specific data. It utilizes a language model (such as OpenAI's GPT-4) to achieve this conversion.

#### Attributes:
- **llm (BaseLLMConnector):** An instance of an LLM connector used for processing queries. This is typically an OpenAI GPT-4 connector.
- **folio (Folio):** An instance of the Folio class used for managing and versioning prompt templates.
- **mappings_handler (MappingsHandler):** A handler responsible for loading various mappings required for query conversion.
- **team_collection:** A MongoDB collection object for accessing team-related data.
- **stat_matchers:** A dictionary mapping sport codes and entities to their respective stat matchers, used to identify relevant statistics for the query.

#### Constructor: `__init__(self, llm: BaseLLMConnector, stat_matchers)`

Initializes the `NlpProcessor` with the necessary dependencies.

- **Args:**
  - `llm (BaseLLMConnector)`: The LLM connector instance.
  - `stat_matchers`: A dictionary mapping sport codes and entities to their respective stat matchers.

#### Method: `convert_to_aql(self, basic_query: str, sport_code: str, entity: str, team_code: str, use_rag: bool = True) -> dict`

Converts a natural language query into a structured AQL format using LLM processing. This method performs several steps to ensure the accurate conversion of queries.

- **Args:**
  - `basic_query (str)`: The natural language query to be converted.
  - `sport_code (str)`: A sport identifier, such as "MFB" for football.
  - `entity (str)`: The target entity for the query, such as "Player" or "Team".
  - `team_code (str)`: A team identifier code.
  - `use_rag (bool, optional)`: A flag indicating whether to use Retrieval-Augmented Generation (RAG) for stat matching. Defaults to `True`.

- **Returns:**
  - A dictionary containing the structured AQL, which includes:
    - `conditions`: Query conditions.
    - `qualifiers`: Query qualifiers, including team context.
    - `stat_period`: The statistical period for the query.

- **Raises:**
  - `ValueError`: Raised if the team is not found or if the LLM response is invalid.

#### Implementation Steps:

1. **Retrieve Team Context:**
   - Fetches the team name using the `team_code` from the MongoDB `team_collection`. Raises a `ValueError` if the team is not found.

2. **Load Prompt Template:**
   - Retrieves the latest prompt version from Folio using the `get_prompt` method. Raises a `ValueError` if the prompt is missing.

3. **Load Stat Mapping and Query Samples:**
   - Depending on the `use_rag` flag, either employs the `stat_matchers` to match stats dynamically or uses pre-configured mappings from `mappings_handler`.

4. **Format and Render Prompt:**
   - Uses the Jinja2 `Template` to dynamically format the prompt with the query details, context, stat mappings, and other necessary data.

5. **Process Query with LLM:**
   - Sends the formatted prompt to the LLM to generate an AQL response.

6. **Parse and Validate Response:**
   - Parses the response to ensure it is in JSON format, validates the structure, and ensures team context is included in the qualifiers.

## Important Details and Dependencies

- **Dependencies:**
  - **time:** Python module for tracking time intervals.
  - **typing.List:** Used for type hinting.
  - **OpenAIConnector, BaseLLMConnector:** Modules for connecting to and utilizing language models.
  - **Folio:** Manages prompt version control.
  - **MappingsHandler:** Handles dynamic loading of mappings.
  - **MongoDB (`db`):** Used to store and retrieve team data.
  - **Jinja2 Template:** Used for rendering dynamic templates.
  - **Constants (Qualifiers, General):** Used for consistent key definitions across the script.

- **Error Handling:**
  - The script includes robust error handling for missing data, invalid team codes, and malformed LLM responses.

By providing a structured approach to natural language processing, the `NlpProcessor` class enhances the ability to generate AQL queries dynamically and accurately. This documentation captures the purpose and functionality of the script in detail, making it easier to understand and extend.
