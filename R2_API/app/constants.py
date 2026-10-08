from enum import Enum

QUALIFIERS_MAPPING = {
    "playerName" : "player_name",
    "playerClass": "player_class",
    "teamName" : "team_name",
    "teamConferenceName": "conference_name",
    "opponentTeamName": "opponent_team_name",
    "opponentConferenceName": "opponent_conference_name",
    "position" : "position",
    "season" : "season",
    "teamCode" : "team_code"
}

class Qualifiers(Enum):
    """Enumeration of valid qualifier fields used for filtering queries.
    
    These qualifiers are used to filter and constrain database queries based on 
    player, team, and game attributes.
    """
    PLAYER_NAME = "playerName"
    PLAYER_CLASS = "playerClass" 
    TEAM_NAME = "teamName"
    TEAM_CONFERENCE_NAME = "teamConferenceName"
    OPPONENT_TEAM_NAME = "opponentTeamName"
    POSITION = "position"
    OPPONENT_CONFERENCE_NAME = "opponentConferenceName"
    SEASON = "season"
    TEAM_CODE = "teamCode"

class SortingFields(Enum):
    """Enumeration of valid fields that can be used for sorting query results.
    
    These fields represent the available options for ordering and sorting the 
    data returned from database queries.
    """
    PLAYER_NAME = "playername"
    TEAM_NAME = "teamname"
    SEASON = "season"
    POSITION = "position"
    CONDITIONS = "conditions"
    QUALIFIERS = "qualifiers"
    GAMEDATE = "game_date"
    STREAKLENGTH = "streak_length"
    PLAYERCLASS = "playerClass"
    OPPONENTTEAMNAME = "opponentTeamName"
    QUERYTYPE = "query_type"

class DatabaseTables(Enum):
    """Enumeration of database table names used in the application.
    
    Defines the canonical names of tables storing player and team statistics.
    """
    PLAYER_STATS = "player_game_statistics"
    TEAM_STATS = "team_game_statistics"

class SortOrders(Enum):
    """Enumeration of valid sort orders for query results.
    
    Defines ascending and descending sort order options.
    """
    ASC = "ASC"
    DESC = "DESC"

class QueryTypes(Enum):
    """Enumeration of supported query types for statistical analysis.
    
    Defines the different types of statistical queries that can be performed:
    - basic: Standard statistical queries
    - min: Minimum value queries
    - max: Maximum value queries
    - ltw: Last time when queries
    - streak: Streak analysis queries
    """
    BASIC = "basic"
    MIN = "min"
    MAX = "max"
    LTW = "ltw"
    STREAK = "streak"

class PlayerClass(Enum):
    """Enumeration of valid NCAA player classification years.
    
    Defines the standard academic classifications for college athletes.
    """
    FRESHMAN = 'FRESHMAN'
    JUNIOR = 'JUNIOR'
    SENIOR = 'SENIOR'
    SOPHOMORE = 'SOPHOMORE'

class Positions(Enum):
    """Enumeration of valid player positions across supported sports.
    
    Includes positions for:
    - Football (FB, QB, WR, etc.)
    - Men's Basketball (C, F, G)
    """
    # Football positions
    CB = 'CB'  # Cornerback
    DB = 'DB'  # Defensive Back
    DE = 'DE'  # Defensive End
    DL = 'DL'  # Defensive Line
    DT = 'DT'  # Defensive Tackle
    FB = 'FB'  # Fullback
    K = 'K'    # Kicker
    LB = 'LB'  # Linebacker
    LS = 'LS'  # Long Snapper
    OC = 'OC'  # Center
    OG = 'OG'  # Offensive Guard
    OL = 'OL'  # Offensive Line
    OT = 'OT'  # Offensive Tackle
    P = 'P'    # Punter
    QB = 'QB'  # Quarterback
    RB = 'RB'  # Running Back
    S = 'S'    # Safety
    TE = 'TE'  # Tight End
    WR = 'WR'  # Wide Receiver

    # Men's Basketball positions
    C = 'C'    # Center
    F = 'F'    # Forward
    G = 'G'    # Guard

class UserDataAuthentication(Enum):
    """Enumeration of authentication and user data fields.
    
    Defines the fields used for user authentication, session management,
    and user profile data.
    """
    EMAIL = "email"
    TEAM = "team"
    SPORTS = "sports"
    USERNAME = "username"
    ISACTIVE = "isActive"
    HASHEDPWD = "hashedPwd"
    USERID = "userid"
    ACCESSTOKEN = "access_token"
    REFRESHTOKEN = "refresh_token"
    TOKENTYPE = "token_type"
    BEARER = "bearer"
    TERMSAGREED = "termsAgreed"

class MappingsHandlerTerms(Enum):
    """Enumeration of mapping configuration file names and paths.
    
    Defines the standard file names and paths for various mapping configurations
    used throughout the application.
    """
    TABLE_MAPPING = "table_mapping.json"
    FIELDS_MAPPING = "fields_mapping.json"
    FILTER_MAPPINGS = "filter_mappings.json"
    POSITION_MAPPINGS = "pos_mapping.json"
    METADATA_MAPPINGS = "metadata_mapping.json"
    QUERY_SAMPLES = "query_samples"
    STAT_MAPPING_FOLDER = "stat_mapping"
    DATA_CONFIG = "data_config"
    MAPPINGS_ROOT = "mappings"

class General(Enum):
    """Enumeration of general purpose constants used across the application.
    
    Defines common terms and fields used in various parts of the application.
    """
    STAT = "stat"
    DESCRIPTION = "description"
    STAT_PERIOD = "stat_period"

class LLMModels(Enum):
    """Enumeration of supported Language Learning Models and their configurations.
    
    Defines available LLM models and their associated API keys across different providers:
    - OpenAI models (GPT-4)
    - Google models (Gemini)
    - Meta models (Llama)
    - Other providers (Groq, Gemma)
    """
    BASE = "base"
    GPT4 = "gpt-4o"
    GPT_MINI = "gpt-4o-mini"
    OPENAI_API_KEY = "OPENAI_API_KEY"
    GEMINI_FLASH = "gemini-2.0-flash"      
    GEMINI_FLASH_LITE = "gemini-2.0-flash-lite"
    GEMINI_API_KEY = "GEMINI_API_KEY"
    LLAMA_1 = "llama-3.2-1b-preview"
    LLAMA_8 = "llama3-8b-8192"
    LLAMA_70 = "llama-3.3-70b-versatile"
    GROQ_API_KEY = "GROQ_API_KEY"
    GEMMA = "gemma2-9b-it"
    GPT_O4_MINI = "o4-mini-2025-04-16"
    GPT4_1_MINI = "gpt-4.1-mini"
    GPT4_1 = "gpt-4.1"

class PostgreSQL(Enum):
    """Enumeration of PostgreSQL database configuration environment variables.
    
    Defines the expected environment variables needed for PostgreSQL database connection.
    """
    PG_DB = "PG_DB"           # Database name
    PG_USER = "PG_USER"       # Database user
    PG_PASSWORD = "PG_PASSWORD"# Database password
    PG_HOST = "PG_HOST"       # Database host
    PG_PORT = "PG_PORT"       # Database port