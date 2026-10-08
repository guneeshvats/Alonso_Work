from pydantic import BaseModel, conint, Field
from typing import Optional, Dict, List, Union


from app.llms import LLMConnectors, LLMModels  # Import Enum for validation

class SearchRequest(BaseModel):
    """
    Represents a search request model containing query parameters for structured data retrieval.
    
    Attributes:
        BasicQuery (str): The main search query text provided by the user
        SportCode (str): Code identifying the sport to search within
        TeamCode (Optional[str]): Team identifier code, if searching for specific team data
        AQLOnly (Optional[bool]): If True, returns only the AQL query without executing it
        Entity (str): The type of entity to search for (e.g., "Player", "Team")
        TimePeriod (Optional[str]): Time period for stats aggregation, defaults to "Game"
        GamePeriod (Optional[str]): Specific period within a game to filter by
        PageNumber (int): Current page number for pagination, must be >= 1
        PageSize (int): Number of results per page, between 1-100
        Filters (Dict[str, Union[str, List[str]]]): Additional filtering criteria
        SortBy (Optional[str]): Field name to sort results by
        SortOrder (Optional[str]): Sort direction, either "ASC" or "DESC"
        Llm (LLMConnectors): Language model connector to use, defaults to OpenAI
        LlmModel (LLMModels): Specific language model to use, defaults to GPT-Mini
        UseRAG (bool): Whether to use RAG for stat shortlisting, defaults to True
    """
    BasicQuery: str
    SportCode: str
    TeamCode: Optional[str] = None
    AQLOnly: Optional[bool] = False
    Entity: str
    TimePeriod: Optional[str] = "Game"
    GamePeriod: Optional[str] = None
    PageNumber: conint(ge=1) = Field(default=1, description="Page number (must be 1 or greater)")
    PageSize: conint(ge=1, le=100) = Field(default=10, description="Page size (between 1 and 100)")
    Filters: Dict[str, Union[str, List[str]]] = Field(default={}, description="Filters applied to the search")
    SortBy: Optional[str] = Field(None, description="Sorting field")
    SortOrder: Optional[str] = Field(None, pattern="^(ASC|DESC)$", description="Sort order (ASC or DESC)")
    Llm: LLMConnectors = Field(default=LLMConnectors.OPENAI, description="LLM connector type")
    LlmModel: LLMModels = Field(default=LLMModels.GPT_MINI, description="LLM model type")
    UseRAG: bool = Field(default=True, description="Use RAG to shortlist stats before sending to LLM")
    aql_output: Optional[dict] = None


class ExportRequest(BaseModel):
    sql: str
    sport_code: str
    entity: str
    stat_columns: Optional[List[str]] = []
    limit: Optional[int] = 0
    offset: Optional[int] = 0


class SearchResponse(BaseModel):
    """
    Represents a structured response from a search query, containing retrieved data and metadata.
    
    Attributes:
        count (int): Total number of results found
        results (List[dict]): List of search results matching the query
        aql_output (dict): The generated AQL query and its components
        sql_query (str): The SQL query generated from the AQL
        inference_time (float): Time taken for query inference in seconds
        positions (Optional[List[str]]): List of player positions found in results
        classes (Optional[List[str]]): List of player classes/years found in results
        teams (Optional[List[str]]): List of team names found in results
    """
    count: int
    results: List[dict]
    aql_output: dict
    sql_query: str
    inference_time: float
    query_execution_time: float
    mongo_execution_time: float
    # Optional fields for additional result metadata
    positions: Optional[List[str]] = None
    classes: Optional[List[str]] = None
    teams: Optional[List[str]] = None


