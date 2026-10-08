from fastapi import APIRouter, HTTPException, Depends, Query
from app.models.player_dashboard_models import PlayerProfileRequest, PlayerProfileResponse, PlayerRecordsRequest, PlayerRecordsResponse, PlayerHighsRequest, PlayerHighsResponse, PlayerGameLogsRequest, PlayerGameLogsResponse,PlayerStreaksResponse, PlayerStreaksRequest, MappingRequest
from app.api.routes.auth import verify_token 
from app.db.pgsql_adapter import PGSQLAdapter
import logging
from psycopg2 import pool
from decouple import config
from app.constants import PostgreSQL

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


router = APIRouter()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/player_profile",response_model=PlayerProfileResponse )

async def get_player_profile(request: PlayerProfileRequest,):
    """
    endpoint for retrieving player profile information.
    
    This endpoint fetches detailed player profile data from the database based on the provided
    player ID and sport code. It returns a PlayerProfileResponse containing player details.
    
    Args:
        request (PlayerProfileRequest): Contains player ID and sport code
        username (str): Authenticated username from JWT token
        
    Returns:
        PlayerProfileResponse: Contains player profile information
        
    Raises:
        HTTPException: For various error conditions with appropriate status codes
    """
    try:
        # logger.info(f"User '{username}' is making a player profile request.")
        logger.info(f"Received player profile request: {request.model_dump()}")
        pgsql_adapter = PGSQLAdapter(pg_pool)

        player_data = pgsql_adapter.execute_player_profile(
            sport_code=request.SportCode,
            entity="Player",
            player_id=request.Player_id)

        # print(player_data)

        return PlayerProfileResponse(**player_data)

    except Exception as e:
        logger.error(f"Error in get_player_profile: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")



@router.post("/player-game-logs")

async def get_player_game_logs(request: PlayerGameLogsRequest):
    """
    endpoint for retrieving player game logs.
    
    This endpoint fetches detailed player game logs data from the database based on the provided
    player ID and sport code. It returns a PlayerGameLogsResponse containing player game logs.
    
    Args:
        request (PlayerGameLogsRequest): Contains player ID and sport code
        username (str): Authenticated username from JWT token
        
    Returns:
        PlayerGameLogsResponse: Contains player game logs information
        
    Raises:
        HTTPException: For various error conditions with appropriate status codes
    """
    try:
        # logger.info(f"User '{username}' is making a player profile request.")
        logger.info(f"Received player game logs request: {request.model_dump()}")
        pgsql_adapter = PGSQLAdapter(pg_pool)
        player_data = pgsql_adapter.execute_player_game_logs(
            sport_code=request.SportCode,
            entity="Player",
            season=request.Season,
            player_id=request.Player_id)

        return player_data

    except Exception as e:
        logger.error(f"Error in get_player_game_logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")




@router.post("/player-records", response_model=PlayerRecordsResponse)

async def get_player_records(request: PlayerRecordsRequest):
    """
    endpoint for retrieving player records.
    
    This endpoint fetches detailed player records data from the database based on the provided
    player ID and sport code. It returns a PlayerRecordsResponse containing player records.
    
    Args:
        request (PlayerProfileRequest): Contains player ID and sport code
        username (str): Authenticated username from JWT token
        
    Returns:
        PlayerProfileResponse: Contains player profile information
        
    Raises:
        HTTPException: For various error conditions with appropriate status codes
    """
    try:
        # logger.info(f"User '{username}' is making a player profile request.")
        logger.info(f"Received player record request: {request.model_dump()}")
        pgsql_adapter = PGSQLAdapter(pg_pool)
        player_data = pgsql_adapter.execute_player_records(
            sport_code=request.SportCode,
            entity="Player",
            player_id=request.Player_id,
            teamcode=request.TeamCode,
            stat_period=request.StatPeriod,
            rank_threshold=request.RankThreshold,
        )

        # print(player_data)

        return PlayerRecordsResponse(**player_data)

    except Exception as e:
        logger.error(f"Error in get_player_profile: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")



@router.post("/player-highs", response_model=PlayerHighsResponse)
async def get_player_highs(request: PlayerHighsRequest):
    """
    endpoint for retrieving player records.
    
    This endpoint fetches detailed player records data from the database based on the provided
    player ID and sport code. It returns a PlayerRecordsResponse containing player records.
    
    Args:
        request (PlayerProfileRequest): Contains player ID and sport code
        username (str): Authenticated username from JWT token
        
    Returns:
        PlayerProfileResponse: Contains player profile information
        
    Raises:
        HTTPException: For various error conditions with appropriate status codes
    """
    try:
        # logger.info(f"User '{username}' is making a player profile request.")
        logger.info(f"Received player record request: {request.model_dump()}")
        pgsql_adapter = PGSQLAdapter(pg_pool)
        player_highs = pgsql_adapter.execute_player_highs(
            sport_code=request.SportCode,
            entity="Player",
            player_id=request.Player_id,
            stat_period=request.StatPeriod)

        return PlayerHighsResponse(**player_highs)


    except Exception as e:
        logger.error(f"Error in get_player_profile: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
    

@router.get('/player-streaks-mapping')
async def get_player_streaks_category(
    sport_code: str = Query(..., alias="SportCode", description="The sport code"),
    playerposition: str = Query("ALL", alias="playerposition", description="The player position (defaults to ALL if not provided)"),
):
    """
    Retrieves player streaks category mapping based on sport code and player position.
    """
    try:
        pgsql_adapter = PGSQLAdapter(pg_pool)

        player_streaks_category = pgsql_adapter.fetch_streaks_mapping(
            sport_code=sport_code,
            entity="Player",
        )
        return player_streaks_category[playerposition]
    except KeyError as ke:
        logger.error(f"KeyError: Player position '{playerposition}' not found in player_streaks_category. {ke}")
        raise HTTPException(status_code=404, detail=f"Player position '{playerposition}' not found")
    except Exception as e:
        logger.error(f"API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/player-streaks", response_model=PlayerStreaksResponse)
async def get_player_streaks(request: PlayerStreaksRequest):

    try:
        logger.info(f"Received player record request: {request.model_dump()}")
        pgsql_adapter = PGSQLAdapter(pg_pool)
        player_streaks = pgsql_adapter.get_player_streaks(
            sport_code=request.SportCode,
            entity="Player",  
            player_id=request.Player_id,
            teamcode=request.TeamCode,
            stat=request.stat,
            stat_value=request.stat_value,
            streak_length=request.streak_length
        )

        return PlayerStreaksResponse(**player_streaks)  
    except Exception as e:
        logger.error(f"API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

