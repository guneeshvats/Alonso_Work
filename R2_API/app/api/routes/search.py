"""
Search API Module

This module provides endpoints for searching and retrieving data from the R2 system.
It handles both authenticated search requests and public name suggestion requests.
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.search_models import SearchRequest, SearchResponse, ExportRequest
from fastapi.responses import StreamingResponse
from app.api.routes.auth import verify_token 
from app.services.nlp_processor import NlpProcessor
from app.services.sql_builder import SQLBuilder
from app.db.pgsql_adapter import PGSQLAdapter
from app.llms import get_llm_connector
import logging
import time
import io
from app.db.mongo_connection import db
from app.constants import PlayerClass, Positions, SortingFields, QueryTypes, Qualifiers, PostgreSQL
from app.services.stat_matcher import StatMatcher, STModelChoice
from pydantic import BaseModel
from typing import List
from app.data_config.mappings.mappings_handler import MappingsHandler
import pandas as pd
from decouple import config

# Initialize core dependencies
router = APIRouter()
sql_builder = SQLBuilder()
team_collection = db['teams']
roster_collection = db['ActiveRoster']
mappings_handler = MappingsHandler()
team_start_time = time.time()
TEAMS = [team['teamName'] for team in team_collection.find()]
teams_end_time = time.time()

print(f"Loaded teams in {teams_end_time - team_start_time} seconds")
# Load statistical matchers at startup
s = time.time()
STAT_MATCHERS = StatMatcher.get_all_stat_matchers()
#STAT_MATCHERS = None
e = time.time()
print(f"Time taken to load stat_matchers: {e-s}")


from psycopg2 import pool

pg_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    database=config(PostgreSQL.PG_DB.value),
    user=config(PostgreSQL.PG_USER.value),
    password=config(PostgreSQL.PG_PASSWORD.value),
    host=config(PostgreSQL.PG_HOST.value),
    port=config(PostgreSQL.PG_PORT.value),
    #
    # sslmode="disable"  # optional: disable for speed testing
)

print(pg_pool)

def get_pos_class_team_values(sport_code : str, qualifiers: dict):
    """
    Dynamically fetch valid positions, player classes, and teams based on sport code and qualifiers.
    
    This function returns appropriate values for dropdown menus and filters in the UI.
    Values are filtered based on sport code and existing qualifiers to prevent redundant options.

    Args:
        sport_code (str): Sport identifier code (e.g. "MFB" for football, "MBB" for basketball)
        qualifiers (dict): Dictionary of existing query qualifiers that may affect available options

    Returns:
        tuple: Contains three elements:
            - positions (list): Available positions for the sport, or None if already qualified
            - player_classes (list): Available class years, or None if already qualified
            - teams (list): Available team names, or None if already qualified
    """
    if sport_code == "MFB":
        positions = [
            Positions.CB.value,
            Positions.DB.value,
            Positions.DE.value,
            Positions.DL.value,
            Positions.DT.value,
            Positions.FB.value,
            Positions.K.value,
            Positions.LB.value,
            Positions.LS.value,
            Positions.OC.value,
            Positions.OG.value,
            Positions.OL.value,
            Positions.OT.value,
            Positions.P.value,
            Positions.QB.value,
            Positions.RB.value,
            Positions.S.value,
            Positions.TE.value,
            Positions.WR.value
        ]
    elif sport_code == "MBB":
        positions = [
            Positions.C.value, 
            Positions.F.value,
            Positions.G.value
        ]
    else :
        positions = []

    # Only set player_classes for MFB 
    player_classes = None
    if sport_code == "MFB":
        player_classes = [
            "FR",
            "SO",
            "JR",
            "SR",
            "GR",
            "R - FR",
            "R - JR",
            "R - SO",
            "R - SR",
            "RS",
            "5TH"
        ]
    elif sport_code == "MBB":
        player_classes = [
            "FRESHMAN",
            "SOPHOMORE",
            "JUNIOR",
            "SENIOR"
        ]
    # Exclude options that are already qualified in the query
    if SortingFields.POSITION.value in qualifiers:
        positions = None
    if SortingFields.PLAYERCLASS.value in qualifiers:
        player_classes = None
    if SortingFields.OPPONENTTEAMNAME.value in qualifiers:
        teams = None

    return positions, player_classes, TEAMS


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/search", response_model=SearchResponse)
async def search_players(request: SearchRequest, username: str = Depends(verify_token)):
    """
    Protected endpoint for executing complex search queries across sports data.
    
    This endpoint processes natural language queries, converts them to structured AQL,
    generates SQL, executes the query, and returns formatted results. It supports:
    - Natural language query processing
    - Multiple sport codes and entities
    - Pagination and sorting
    - Advanced filtering
    - Optional RAG (Retrieval Augmented Generation)
    
    Args:
        request (SearchRequest): Contains search parameters including query text, filters, and pagination
        username (str): Authenticated username from JWT token
        
    Returns:
        SearchResponse: Contains:
            - Search results with count
            - Generated AQL and SQL
            - Processing time metrics
            - Available filter options
            
    Raises:
        HTTPException: For various error conditions with appropriate status codes
    """
    try:
        logger.info(f"User '{username}' is making a search request.")
        logger.info(f"Received search request: {request.dict()}")

        # Step 1: Convert Natural Language Query to AQL
        llm_connector = get_llm_connector(request.Llm, request.LlmModel)
        nlp_processor = NlpProcessor(llm_connector, stat_matchers=STAT_MATCHERS)
        start_time = time.time()

        if request.aql_output:
            aql_output = request.aql_output
        else:
            aql_output = nlp_processor.convert_to_aql(
                request.BasicQuery,
                request.SportCode,
                request.Entity,
                request.TeamCode,
                use_rag=request.UseRAG)
            logger.info(f" Generated AQL: {aql_output}")
        end_time = time.time()

        print(f"Time taken for AQL generation: {end_time - start_time}")

        if request.AQLOnly:
            logger.info("AQLOnly flag is set to True. Skipping SQL Execution.")
            return SearchResponse(
                count=0,
                results=[], 
                aql_output=aql_output,
                sql_query="",
                inference_time = end_time - start_time,
                query_execution_time=0,
                mongo_execution_time=0
            )

        # Initialize and validate qualifiers
        if 'qualifiers' not in aql_output or not isinstance(aql_output['qualifiers'], dict):
            aql_output['qualifiers'] = {}

        # Ensure team information is properly set
        team_code = None
        if Qualifiers.TEAM_NAME.value not in aql_output['qualifiers']:
            team_doc = team_collection.find_one({Qualifiers.TEAM_CODE.value: request.TeamCode})
            if team_doc and Qualifiers.TEAM_NAME.value in team_doc:
                aql_output['qualifiers'][Qualifiers.TEAM_NAME.value] = team_doc[Qualifiers.TEAM_NAME.value]

        if Qualifiers.TEAM_NAME.value in aql_output['qualifiers']:

            team_name = aql_output['qualifiers'][Qualifiers.TEAM_NAME.value]
            if team_name != "ALL":
                team_doc = team_collection.find_one({Qualifiers.TEAM_NAME.value: team_name})
                if not team_doc or Qualifiers.TEAM_CODE.value not in team_doc:
                    team_code = None
                else:
                    team_code = team_doc[Qualifiers.TEAM_CODE.value]
            else:
                del aql_output['qualifiers'][Qualifiers.TEAM_NAME.value]

        # Process sorting requirements
        sort_by = request.SortBy
        if sort_by:
            sort_by_clean = sort_by.strip().lower()

            # Check metadata fields first
            metadata_mapping = mappings_handler.get_metadata_mapping()
            metadata_values = {v.strip().lower() for v in metadata_mapping.values()}
            
            if sort_by_clean in metadata_values:
                logger.info(f"sort_by '{sort_by}' matched metadata field — using as-is")
                for key, value in metadata_mapping.items():
                    if value.strip().lower() == sort_by_clean:
                        sort_by = key
                        logger.info(f"sort_by '{request.SortBy}' matched metadata value '{value}', using key '{key}'")
                        break
            else:
                # Fall back to stat mapping
                stat_mappings = mappings_handler.get_stat_mapping(request.SportCode, request.Entity)
                logger.info(f"sort_by '{sort_by}' not in metadata fields. Checking stat mappings...")

                for mapping in stat_mappings:
                    short_label = mapping.get('short_label', '').strip().lower()
                    if short_label == sort_by_clean:
                        sort_by = mapping['stat']
                        logger.info(f"Mapped sort_by '{request.SortBy}' to stat '{sort_by}'")
                        break
                else:
                    logger.warning(f"No match found for sort_by '{request.SortBy}' in stat mappings")

        # Generate SQL queries
        sql_query, count_query, selected_columns, stat_columns = sql_builder.convert_aql_to_sql(
            aql_output, 
            request.SportCode, 
            request.Entity, 
            request.Filters, 
            query_type=aql_output.get(SortingFields.QUERYTYPE.value, QueryTypes.BASIC.value), 
            limit=request.PageSize, 
            offset=(request.PageNumber - 1) * request.PageSize,
            sort_by=sort_by,
            sort_order=request.SortOrder,
            team_code=team_code,
        )
        logger.info(f" Generated SQL Query: {sql_query}")

        # Execute queries and fetch results
        s_pg_init = time.time()
        db_adapter = PGSQLAdapter(pg_pool)
        e_pg_init = time.time()
        print(f"PG init took {e_pg_init-s_pg_init} seconds")
        start_time_q = time.time()

        results, total_count = db_adapter.execute_query(
            sql_query, 
            count_query, 
            selected_columns, 
            request.SportCode, 
            request.Entity, 
            stat_columns
            )
        end_time_q = time.time()

        print(f"SQL query took {end_time_q-start_time_q} seconds")
        logger.info(f" Query executed successfully. Retrieved {total_count} records.")

        # Get filter options
        qualifiers = aql_output.get(SortingFields.QUALIFIERS.value, {})
        start_time_mongo = time.time()
        positions, player_classes, teams = get_pos_class_team_values(request.SportCode, qualifiers)
        end_time_mongo = time.time()

        db_adapter.close()
        return SearchResponse(
            count=total_count,
            results=results,
            aql_output=aql_output,
            sql_query=sql_query,
            inference_time = end_time - start_time,
            query_execution_time = end_time_q - start_time_q,
            mongo_execution_time = end_time_mongo - start_time_mongo,
            positions=positions,
            classes=player_classes,
            teams=teams
        )

    except Exception as e:
        logger.error(f" Error in search_players: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")




@router.post("/export")
async def export_data(request: ExportRequest, username: str = Depends(verify_token)):
    db_adapter = PGSQLAdapter(pg_pool)



    results, total_count = db_adapter.execute_query(
        request.sql,
        None,
        [],
        request.sport_code,
        request.entity,
        request.stat_columns
    )

    all_res = []
    for result in results:
        res = result["metadata"] | result["stats"]
        all_res.append(res)

    df = pd.DataFrame(all_res)
    print(df)
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    response = StreamingResponse(iter([stream.getvalue()]),
                                 media_type="text/csv"
                                 )
    response.headers["Content-Disposition"] = "attachment; filename=export.csv"
    db_adapter.close()
    return response



class NameSuggestionsRequest(BaseModel):
    """
    Model for name suggestion requests.
    
    Attributes:
        SportCode (str): Code identifying the sport (e.g. "MFB", "MBB")
        Entity (str): Type of entity to search ("Player" or "Team")
        Prefix (str): Search prefix to match against names
    """
    SportCode: str
    Entity: str
    Prefix: str

class NameSuggestionsResponse(BaseModel):
    """
    Model for name suggestion responses.
    
    Attributes:
        Suggestions (List[str]): List of matching name suggestions
    """
    Suggestions: List[str]

# Router for public endpoints
public_router = APIRouter()

@public_router.post("/name-suggestions", response_model=NameSuggestionsResponse)
async def post_name_suggestions(request: NameSuggestionsRequest):
    """
    Public endpoint that provides auto-complete suggestions for player and team names.
    
    Performs case-insensitive prefix matching against player names or team names
    depending on the entity type specified. Returns up to 10 matching suggestions.
    
    Args:
        request (NameSuggestionsRequest): Contains sport code, entity type, and search prefix
        
    Returns:
        NameSuggestionsResponse: List of matching name suggestions
        
    Raises:
        HTTPException: If no matches found (404) or for server errors (500)
    """
    try:
        logger.info(f"Received suggestion request: {request.dict()}")
        
        sport_code = request.SportCode
        entity = request.Entity
        prefix = request.Prefix
        
        suggestions = []
        
        if entity == "Player":
            # Case-insensitive regex search using MongoDB
            query = {
                "$or": [
                    {"playerName": {"$regex": f"^{prefix}", "$options": "i"}},
                    {"firstName": {"$regex": f"^{prefix}", "$options": "i"}}
                ]
            }
            results = roster_collection.find(query, {"playerName": 1, "_id": 0}).limit(15)
            suggestions = set([doc["playerName"] for doc in results])
            
        elif entity == "Team":
            # Case-insensitive regex search for team names starting with the prefix
            query = {
                "$or": [
                    {"teamName": {"$regex": f"^{prefix}", "$options": "i"}}
                ]
            }
            results = team_collection.find(query, {"teamName": 1, "_id": 0}).limit(10)
            suggestions = [doc["teamName"] for doc in results]
        
        if not suggestions:
            logger.warning(f"No suggestions found for sportCode '{sport_code}', entity '{entity}' and prefix '{prefix}'.")
            raise HTTPException(
                status_code=404,
                detail=f"No suggestions found for sportCode '{sport_code}', entity '{entity}' and prefix '{prefix}'."
            )
        
        logger.info(f"Returning {len(suggestions)} suggestions.")
        return NameSuggestionsResponse(Suggestions=suggestions)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in post_name_suggestions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


