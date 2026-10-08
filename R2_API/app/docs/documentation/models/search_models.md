# Documentation for `search_models.py`

# Technical Documentation for Python Script

## Overview

This Python script defines two data models using Pydantic: `SearchRequest` and `SearchResponse`. These models are designed to facilitate structured data retrieval and response handling in an application, likely related to sports data analysis. The script utilizes Pydantic for data validation and parsing, ensuring that any input or output conforms to the specified schema. The models include fields for search parameters, filters, pagination, and response metadata. Additionally, the script incorporates integration with language model connectors, specifically for generating queries and processing results.

## Detailed Explanation of Each Component

### SearchRequest Class

The `SearchRequest` class is a Pydantic `BaseModel` representing the structure of a search query request. It includes various attributes to specify search criteria and options for query execution. Below is a detailed breakdown of each attribute:

- **BasicQuery (str):** The primary search query text input by the user. This is the core component of the search request.
  
- **SportCode (str):** A string representing the sport's code, allowing the search to be limited to a specific sport.

- **TeamCode (Optional[str]):** An optional string for specifying a particular team, useful for narrowing search results to team-specific data.

- **AQLOnly (Optional[bool]):** A boolean flag that, if set to `True`, indicates that only the AQL query should be returned without being executed.

- **Entity (str):** Specifies the type of entity being searched, such as "Player" or "Team".

- **TimePeriod (Optional[str]):** An optional string defaulting to "Game", which defines the time period for aggregating statistics.

- **GamePeriod (Optional[str]):** Specifies a particular period within a game to filter the results.

- **PageNumber (int):** An integer for pagination that must be greater than or equal to 1, indicating the current page of search results.

- **PageSize (int):** An integer defining the number of results per page, constrained between 1 and 100.

- **Filters (Dict[str, Union[str, List[str]]]):** A dictionary providing additional filtering criteria, allowing for more refined search results.

- **SortBy (Optional[str]):** An optional string that specifies the field name by which results should be sorted.

- **SortOrder (Optional[str]):** An optional string that determines the sort direction, accepting "ASC" for ascending or "DESC" for descending order.

- **Llm (LLMConnectors):** An enumerated type to specify the language model connector, defaulting to `LLMConnectors.OPENAI`.

- **LlmModel (LLMModels):** An enumerated type indicating the specific language model to use, defaulting to `LLMModels.GPT_MINI`.

- **UseRAG (bool):** A boolean flag defaulting to `True`, indicating whether to use Retrieval-Augmented Generation (RAG) for shortlisting statistics before processing with a language model.

### SearchResponse Class

The `SearchResponse` class is a Pydantic `BaseModel` representing the structure of a response returned from a search query. It includes attributes for capturing the results and metadata of the search operation. Below is a detailed explanation of each attribute:

- **count (int):** An integer representing the total number of results found for the search query.

- **results (List[dict]):** A list of dictionaries, each representing a search result that matches the query criteria.

- **aql_output (dict):** A dictionary containing the generated AQL query and its components, providing insights into the query execution process.

- **sql_query (str):** A string representing the SQL query generated from the AQL, used for executing the search against a database.

- **inference_time (float):** A float indicating the time taken for query inference, measured in seconds.

- **positions (Optional[List[str]]):** An optional list of strings denoting player positions found in the search results.

- **classes (Optional[List[str]]):** An optional list of strings representing player classes or years found in the search results.

- **teams (Optional[List[str]]):** An optional list of strings indicating team names found in the search results.

## Implementation Details and Dependencies

- **Pydantic:** The script relies on Pydantic for defining data models and validating data. Pydantic ensures that the data conforms to the specified schemas and provides automatic type conversions and constraints enforcement.

- **Enum Dependencies:** The script imports `LLMConnectors` and `LLMModels` from `app.llms`, which are Enums used to validate the language model connectors and models, respectively. These Enums ensure that only predefined and valid values are used in the search requests.

- **Field Descriptions and Constraints:** The script uses Pydantic's `Field` and `conint` to enforce constraints on fields, such as minimum and maximum values, and to provide descriptive metadata about each field. This facilitates better validation and error handling in applications utilizing these models.
