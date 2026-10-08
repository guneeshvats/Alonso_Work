from pydantic import BaseModel, conint, Field,field_validator
from typing import Optional, Dict, List, Union, Any,Literal
from datetime import date


class PlayerProfileRequest(BaseModel):
    """
    Represents a request for player profile information.
    
    Attributes:
        PlayerName (str): Name of the player
        SportCode (str): Sport identifier code (e.g. "MFB" for football, "MBB" for basketball)
        TeamCode (str): Team identifier code
    """
    Player_id : str
    SportCode : Literal["MFB", "MBB"]


class PlayerProfileResponse(BaseModel):
    """
    Represents a response from a player profile request.
    
    Attributes:
        PlayerName (str): Name of the player
        SportCode (str): Sport identifier code (e.g. "MFB" for football, "MBB" for basketball)
        TeamCode (str): Team identifier code
    """
    PlayerName : str
    SportCode : Literal["MFB", "MBB"]
    TeamName : str
    TeamCode : str
    PlayerPosition : str
    stats : List[Dict[str, Union[str, int, float,Any, None]]]
    stat_mapping : Dict[str, List[str]]
    


class PlayerGameLogsRequest(BaseModel):
    """
    Represents a request for player game logs.
    
    Attributes:
        PlayerName (str): Name of the player
        SportCode (str): Sport identifier code (e.g. "MFB" for football, "MBB" for basketball)
        TeamCode (str): Team identifier code
    """
    Player_id : str
    SportCode : Literal["MFB", "MBB"]
    Season : Optional[int]





class PlayerGameLogsResponse(BaseModel):
    """
    Represents a response from a player game logs request.
    
    Attributes:
        PlayerGameLogs (List[Dict[str, Union[str, int, float,Any, None]]]): List of player game logs
    """
    PlayerName : str
    SportCode : Literal["MFB", "MBB"]
    TeamName : str
    TeamCode : str
    Seasons : List[int]
    PlayerPosition : str
    stats : List[Dict[str, Union[str, int, float,Any, None]]]
    stat_mapping : Dict[str, List[str]]


class PlayerRecordsRequest(BaseModel):
    """
    Represents a request for player records.
    
    Attributes:
        PlayerName (str): Name of the player
        SportCode (str): Sport identifier code (e.g. "MFB" for football, "MBB" for basketball)
        TeamCode (str): Team identifier code
        StatPeriod (str): Statistic period
        RankThreshold (Optional[int]): Minimum rank threshold
    """
    Player_id : str
    SportCode : Literal["MFB", "MBB"]
    TeamCode : str
    StatPeriod: Literal["game","career", "season"] = "game"
    RankThreshold : Optional[int] = 100


class PlayerRecord(BaseModel):
    """Represents a single player performance record for a specific game."""
    stat: str
    value: float
    season: Optional[int] = None
    game_date: Optional[str] = None
    opponent_team_name: Optional[str] = None
    rank: int
    next_rank_value: Optional[float] = None
    
class PlayerRecordsResponse(BaseModel):
    """
    Represents a response from a player records request.
    
    Attributes:
        PlayerRecords (List[Dict[str, Union[str, int, float,Any, None]]]): List of player records
    """
    PlayerRecords : List[PlayerRecord]
    TotalCount : int
    

class PlayerHighsRequest(BaseModel):
    """
    Represents a request for player highs.
    
    Attributes:
        PlayerName (str): Name of the player
        SportCode (str): Sport identifier code (e.g. "MFB" for football, "MBB" for basketball)
        StatPeriod (str): Statistic period
        Limit (Optional[int]): Maximum number of records to return
        Offset (Optional[int]): Number of records to skip
    """
    Player_id : str
    SportCode : Literal["MFB", "MBB"]
    StatPeriod: Literal["career", "season"]



class PlayerHigh(BaseModel):
    """Represents a single player performance high for a specific game."""
    stat: str
    value: float
    season: int
    game_date: str
    opponent_team_name: str
    stat_rank: int


class PlayerHighsResponse(BaseModel):
    """
    Represents a response from a player highs request.
    
    Attributes:
        PlayerHighs (List[Dict[str, Union[str, int, float,Any, None]]]): List of player highs
    """
    PlayerHighs : List[PlayerHigh]
    TotalCount : int



class PlayerStreaksRequest(BaseModel):
    """
    Represents a request for player stats.
    
    Attributes:
        PlayerId (str): Name of the player
        SportCode (str): Sport identifier code (e.g. "MFB" for football, "MBB" for basketball)
        TeamCode (str): Team identifier code
        stat (str): Statistic Name 
        stat_value (int): Statistic Value
        streak_length (int): Streak Length
    """
    Player_id : str
    SportCode : Literal["MFB", "MBB"]
    TeamCode : str
    stat : str
    stat_value : int
    streak_length : int



class PlayerStreaks(BaseModel):
    """
    Represents a response containing player statistics, including streak information.

    Attributes:
        total_count (int): Total number of matching records in the dataset.
        playername (str): Name of the player.
        teamname (str): Name of the player's team.
        streak_length (int): Length of the streak.
        start_game_date (date): Date of the first game in the streak (YYYY-MM-DD).
        start_opponent (str): Name of the opponent in the first game of the streak.
        end_game_date (date): Date of the last game in the streak (YYYY-MM-DD).
        end_opponent (str): Name of the opponent in the last game of the streak.
    """
    player_name: str
    team_name: str
    streak_length: int
    start_game_date: date
    start_opponent: str
    end_game_date: date
    end_opponent: str

    @field_validator('start_game_date', 'end_game_date')
    def parse_date(cls, value):
        if isinstance(value, str):
            return date.fromisoformat(value)
        return value


class PlayerStreaksResponse(BaseModel):
    """
    Represents a response from a player streaks request.
    
    Attributes:
        PlayerStreaks (List[Dict[str, Union[str, int, float,Any, None]]]): List of player streaks
    """
    PlayerStreaks : List[PlayerStreaks]
    TotalCount : int


class MappingRequest(BaseModel):
    SportCode: Literal["MFB", "MBB"]
    playerposition: str


