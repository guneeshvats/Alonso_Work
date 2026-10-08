from pydantic import BaseModel, conint, Field
from typing import Optional, Dict, List, Union

class ReportIssuesRequest(BaseModel):
    """
    Represents a request to report issues with search results.
    
    Attributes:
        Issue (str): Description of the issue
        SearchQuery (str): The search query associated with the issue
    """
    Issue: str
    SearchQuery: str
    count: int
    results: List[dict]
    aql_output: dict
    sql_query: str
    inference_time: float
    positions: Optional[List[str]] = None
    classes: Optional[List[str]] = None
    teams: Optional[List[str]] = None


class ReportIssuesResponse(BaseModel):
    """
    Represents a response from a report issues request.
    
    Attributes:
        Message (str): A success message
    """
    Message: str