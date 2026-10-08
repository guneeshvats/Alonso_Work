from .serializers import *
from datetime import datetime
from decouple import config
from django.conf import settings
from django.core.exceptions import ValidationError
from django.shortcuts import render
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from pprint import pprint
from pymongo import MongoClient, ASCENDING, DESCENDING
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status
import json
import os
from django.core.mail import send_mail

import psycopg2
from .pgsql_adapter import PGSQLAdapter 

# Importing mock data from the separate file
from .mock_data import mock_data
from .nlp_search_pilot import NlpSearch

import logging
import re

# Get MongoDB connection string from environment variables
mongo_uri = config('DB_URI')
db_name = config('DB_NAME')

# Connect to MongoDB using PyMongo
client = MongoClient(mongo_uri)
db = client[db_name]
playergame_collection = db['PlayerGameStatistics']
statmapping_collection = db['stat_mapping']
roster_collection = db['ActiveRoster']
team_collection = db['teams']
query_log_collection = db['AQL_query_log']
issue_collection = db['reported_issues']

logging.basicConfig(
    level=logging.INFO,  # You can set this to DEBUG for more detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger()

# Ensure results directory exists
RESULTS_DIR = "results"
# Ensure the directory exists
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)




@swagger_auto_schema(
    method='post',
    request_body=SearchInputSerializer,
    responses={200: SearchOutputSerializer(many=True)},
)
@api_view(['POST'])
def search_players(request):
    # Validate input using the serializer
    # Using serializers for now as we have mock data stored in Python script
    logger.info(f"Incoming Request Data: {json.dumps(request.data, indent=2)}")
    serializer = SearchInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data

    user_id = validated_data.get('UserId')
    sport_code = validated_data.get('SportCode')
    team_code = validated_data.get('TeamCode')
    basic_query = validated_data.get('BasicQuery')
    entity = validated_data.get('Entity')
    time_period = validated_data.get('TimePeriod')
    game_period = validated_data.get('GamePeriod')
    page_number = validated_data.get('PageNumber')
    page_size = validated_data.get('PageSize')

    # Apply offsets
    # Currently returning all mock data. In the future, we will be filtering based on search criteria 
    #result = mock_data[from_offset:to_offset]
    
    query_filter = {"teamCode": team_code}
    try:
        if page_number < 0 or page_size <= 0:
            raise ValueError("Invalid pagination parameters: page_number and page_size must be positive.")
        skip_value = page_number * page_size
        result = playergame_collection.find(query_filter, {
                "gPersonId": 1,
                "position": 1,
                "playerClass": 1,
                "gameResult": 1,
                "playerName": 1,
                "teamCode": 1,
                "teamName": 1,
                "opponentTeamCode": 1,
                "opponentTeamName": 1,
                "gCompetitionId": 1,
                "academicSeason": 1,
                "gConferenceId": 1,
                "teamConferenceName": 1,
                "gOpponentConferenceId": 1,
                "opponentConferenceName": 1,
                "gMatchId": 1,
                "actualDate": 1,
                "sReceptionsYards": 1,
                "sRushingYardsNet": 1,
                "_id":0
        }).skip(skip_value).limit(page_size)

        result_list = list(result)
            
        # Convert GeniusLabel to AthlyteLabel

        # Get all stat mappings from the statmapping collection
        stat_mapping = {entry['GeniusLabel']: entry['AthlyteLabel'] for entry in statmapping_collection.find()}
        result_list = format_output(result_list, stat_mapping)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    output_serializer = SearchOutputSerializer(result_list, many=True)

    return Response(output_serializer.data)

@swagger_auto_schema(
    method='post',
    request_body=PeriodConfigInputSerializer,
    responses={200: PeriodConfigOutputSerializer},
)
@api_view(['POST'])
def get_period_config(request):
    # Validate input using the serializer
    serializer = PeriodConfigInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    sport_code = validated_data.get('SportCode')

    # Mock configuration data
    # In a real application, you might fetch this data from a database or a configuration file.
    period_config = {
        "MFB": {
            "Player":{
                "Game": {
                    "all_quarters": "All Quarters",
                    "first_quarter": "First Quarter",
                    "second_quarter": "Second Quarter",
                    "third_quarter": "Third Quarter",
                    "fourth_quarter": "Fourth Quarter",
                    "first_half": "First Half",
                    "second_half": "Second Half",
                    "overtime": "Overtime"
                },
                "Season": {
                },
                "Career": {
                }
            },
            "Team": {
                "Game": {
                    "all_quarters": "All Quarters",
                    "first_quarter": "First Quarter",
                    "second_quarter": "Second Quarter",
                    "third_quarter": "Third Quarter",
                    "fourth_quarter": "Fourth Quarter",
                    "first_half": "First Half",
                    "second_half": "Second Half",
                    "overtime": "Overtime"
                },
                "Season": {
                }
            }
        },
        "MBB": {
            "Player":{
                "Game": {
                    "all_quarters": "All Quarters",
                    "first_half": "First Half",
                    "second_half": "Second Half",
                    "overtime": "Overtime"
                },
                "Season": {
                },
                "Career": {
                }
            },
            "Team": {
                "Game": {
                    "all_quarters": "All Quarters",
                    "first_half": "First Half",
                    "second_half": "Second Half",
                    "overtime": "Overtime"
                },
                "Season": {
                }
            }
        },
        "WBB": {
            "Player":{
                "Game": {
                    "all_quarters": "All Quarters",
                    "first_quarter": "First Quarter",
                    "second_quarter": "Second Quarter",
                    "third_quarter": "Third Quarter",
                    "fourth_quarter": "Fourth Quarter",
                    "first_half": "First Half",
                    "second_half": "Second Half",
                    "overtime": "Overtime"
                },
                "Season": {
                },
                "Career": {
                }
            },
            "Team": {
                "Game": {
                    "all_quarters": "All Quarters",
                    "first_quarter": "First Quarter",
                    "second_quarter": "Second Quarter",
                    "third_quarter": "Third Quarter",
                    "fourth_quarter": "Fourth Quarter",
                    "first_half": "First Half",
                    "second_half": "Second Half",
                    "overtime": "Overtime"
                },
                "Season": {
                }
            }
        }
    }

    # Retrieve the configuration for the given SportCode
    config = period_config.get(sport_code.upper(), {})

    if not config:
        return Response(
            {"error": f"No configuration found for SportCode '{sport_code}'"},
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(config, status=status.HTTP_200_OK)


def format_output(result_list, stat_mapping):
    # Replace the GeniusLabel with AthlyteLabel in the result
    map_col_names = {
        "position": "POS",
        "playerClass": "CLASS",
        "gameResult": "RES",
        "playerName": "PLAYER",
        "teamName": "TEAM",
        "opponentTeamName": "OPP",
        "academicSeason": "SEASON",
        "teamConferenceName": "CONF",
        "opponentConferenceName": "OPP_CONF",
        "actualDate": "DATE",
    }         
    for doc in result_list:

        stats_dict = {}

        # Create a copy of the original doc items to avoid modifying during iteration
        new_doc = doc.copy()
        keys_to_delete = []

        for key, value in doc.items():
            if isinstance(key, str) and key in stat_mapping:
                # Replace GeniusLabel with AthlyteLabel
                new_key = stat_mapping[key].upper()
                stats_dict[new_key] = value
                keys_to_delete.append(key)
            if isinstance(key, str) and key in map_col_names:
                # Replace GeniusLabel with AthlyteLabel
                new_key = map_col_names[key]
                new_doc[new_key] = value
                keys_to_delete.append(key)
        new_doc["stats"] = stats_dict
        
        # Update the original document with the new keys and values
        for key in keys_to_delete:
            new_doc.pop(key, None)

        doc.clear()
        doc.update(new_doc)

    return result_list

def get_game_period_mapping():
    game_period_mapping = {
        "All Quarters": {"periodType":"REGULAR", "periodNumber":0},
        "First Quarter": {"periodType":"REGULAR", "periodNumber":1},
        "Second Quarter": {"periodType":"REGULAR", "periodNumber":2},
        "Third Quarter": {"periodType":"REGULAR", "periodNumber":3},
        "Fourth Quarter": {"periodType":"REGULAR", "periodNumber":4},
        "First Half": {"periodType":"HALF", "periodNumber":1},
        "Second Half": {"periodType":"HALF", "periodNumber":2},
        "Overtime": {"periodType":"OVERTIME", "periodNumber":0}
    }
    return game_period_mapping

def get_pos_class_team_values():
    pos = ['CB', 'DB', 'DE', 'DL', 'DT', 'FB', 'K', 'LB', 'LS', 'OC', 'OG', 'OL', 'OT', 'P', 'QB', 'RB', 'S', 'TE', 'WR']
    classes = ['FRESHMAN', 'JUNIOR', 'SENIOR', 'SOPHOMORE']
    teams = [team['teamName'] for team in team_collection.find()]
    return pos, classes, teams


class Common:
    entities = ['player', 'team']
    genius2athlyteshort_mapping = { entity : {
            entry['GeniusLabel'].lower(): entry['AthlyteShortLabel']
            for entry in statmapping_collection.find({"entity" : entity, "R1": True})
        } for entity in entities
    }

    positions, player_classes, teams = get_pos_class_team_values()

class ValidationError(Exception):
    """Custom exception for query validation errors."""
    pass



@swagger_auto_schema(
    method='get',
    operation_summary="Get Stat Mapping by Sport and Entity",
    operation_description=(
        "Retrieve the stat mapping for a given sport and entity type. This API provides the mapping between "
        "AthlyteLabel and GeniusLabel, which is essential for query translation. Defaults to 'MFB' (football) and "
        "'Player' if no parameters are provided."
    ),
    manual_parameters=[
        openapi.Parameter(
            "sportCode",
            openapi.IN_QUERY,
            description="The sport code (e.g., MFB, MBB).",
            type=openapi.TYPE_STRING,
            default="MFB",
        ),
        openapi.Parameter(
            "entity",
            openapi.IN_QUERY,
            description="The entity type (e.g., Player, Team).",
            type=openapi.TYPE_STRING,
            default="Player",
        ),
    ],
    responses={
        200: openapi.Response(
            description="Stat mapping for the specified sport and entity.",
            examples={
                "application/json": {
                    "mapping": {
                        "sRushingYardsNet": "Rushing yards net",
                        "sReceptionsYards": "Reception yards"
                    }
                }
            },
        ),
        400: openapi.Response(
            description="Invalid sport or entity.",
        ),
    },
    tags=["Stat Mapping"],
)
@api_view(['GET'])
def get_stat_mapping(request):
    sport_code = request.GET.get("sportCode", "MFB").upper()
    entity = request.GET.get("entity", "Player").lower()

    try:
        query = {"entity": entity}
        mappings = {
            entry["AthlyteLabel"]: entry["GeniusLabel"]
            for entry in statmapping_collection.find(query)
        }

        if not mappings:
            return Response(
                {"error": f"No mappings found for sportCode '{sport_code}' and entity '{entity}'."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"mapping": mappings}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

def add_to_log(basic_query, query_regex, query_filter, time_period, qualifiers):
    timestamp = datetime.now()  # Get current timestamp
    
    log_data = {
        "basic_query": basic_query,
        "query_regex": query_regex,
        "query_filter": query_filter,
        "time_period": time_period,
        "qualifiers": qualifiers,
        "timestamp": timestamp
    }
    
    query_log_collection.insert_one(log_data)


@swagger_auto_schema(
    method='post',
    operation_summary="Search Players with natural language",
    operation_description=(
        "This API allows users to search for player data based on a combination of filters such as sport code, "
        "entity type, and time/game periods. The `BasicQuery` parameter accepts natural language queries related to stats"
        " which are dynamically mapped to the appropriate database fields. "
        "Example: {\"BasicQuery\": \"rushing yards over 25 and receiving yards greater than 20\"}" 
    ),
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "BasicQuery": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Logical query to filter player data.",
                example="rushing yards over 25 and receiving yards greater than 20"
            ),

            "SportCode": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Sport code to filter players (e.g., 'MFB').",
                example="MFB"
            ),
            "TeamCode": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="TeamCode to filter teams.",
                example="31"
            ),
            "Entity": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Entity type to search (e.g., 'Player').",
                example="Player"
            ),
            "TimePeriod": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Game, Season or Career.",
                example="Game"
            ),
            "GamePeriod": openapi.Schema(
                type=openapi.TYPE_STRING,
                description="Period within game. Eg. All Quarters, First Quarter, Overtime",
                example="All Quarters"
            ),
            "PageNumber": openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="PageNumber for Pagination.",
                example=1
            ),
            "PageSize": openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description="PageSize for Pagination.",
                example=10
            ),
        },
        required=["BasicQuery"],
    ),
    responses={
        200: openapi.Response(
            description="List of players matching the search criteria.",
            schema=SearchOutputSerializer(many=True),
            examples={
                "application/json": [
                    {
                        "gPersonId": "12345",
                        "playerName": "John Doe",
                        "position": "Quarterback",
                        "teamName": "Team A",
                        "academicSeason": 2024,
                        "Reception yards": 100,
                        "Rushing yards net": 50,
                    }
                ]
            },
        ),

        400: openapi.Response(
            description="Invalid request format or validation error.",
        ),
        500: openapi.Response(
            description="Server error while processing the request.",
        ),
    },
    tags=["Search NL"],
)




@api_view(['POST'])
def search_players_nl(request):
    """
    Process a Natural Language query, convert it to AQL, generate SQL, execute the query, and return results.
    """
    logger.info(f"Incoming Request Data: {json.dumps(request.data, indent=2)}")

    serializer = SearchInputSerializer(data=request.data)
    if not serializer.is_valid():
        logger.error(f"Serializer Errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    user_id = validated_data.get('UserId')
    sport_code = validated_data.get('SportCode')
    team_code = validated_data.get('TeamCode')
    basic_query = validated_data.get('BasicQuery')
    entity = validated_data.get('Entity')
    time_period = validated_data.get('TimePeriod')
    game_period = validated_data.get('GamePeriod')
    page_number = validated_data.get('PageNumber', 1)
    page_size = validated_data.get('PageSize', 10)
    filters = validated_data.get('Filters', {})
    aql_only = validated_data.get('AQLOnly', False)

    team_name = team_collection.find({"teamCode": str(team_code)})[0]["teamName"]
    context = {"teamName" : team_name}

    if not isinstance(filters, dict):
        filters = {}
    sort_by = validated_data.get('SortBy', None)
    sort_order = validated_data.get('SortOrder', 'asc')

    # Initialize PostgreSQL Adapter
    pg_adapter = PGSQLAdapter()
    result_list = []
    column_names = []
    sql_query = None
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')  # Unique timestamp for files
    selected_columns = []
    #  Initialize response variables
    sql_query_output = ""  
    aql_output = {}

    positions, player_classes, teams = Common.positions, Common.player_classes, Common.teams

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    if basic_query:
        try:
            #  Step 1: Convert Natural Language Query to AQL
            nlp_search = NlpSearch(logger)
            query_regex, time_period, qualifiers, query_type, streak_len = nlp_search.generate_search_queries(basic_query, context)

            if ("opponentTeamName" in qualifiers) and (
                    qualifiers["opponentTeamName"].lower() == context["teamName"].lower()) and (
                    'teamName' not in qualifiers):
                # If my team is given as the opponent team without specifying any teamName, then teamName should be "any"

                #qualifiers["teamName"] = "any"
                team_code = None

            if ("teamName" in qualifiers) and (qualifiers["teamName"] == "any"):
                del qualifiers["teamName"]
                team_code = None

            #  Construct AQL Query
            aql_output = {
                "query": basic_query,
                "query_type": query_type,
                "entity": entity.lower(),
                "qualifier": qualifiers,
                "stat_period": time_period.lower(),
                "conditions": query_regex,
                "streak_len" : streak_len,
            }



            if aql_only:
                return Response({
                    "count": 0,
                    "results": [],
                    "aql_output": aql_output,  # Fix: Now initialized correctly
                    "sql_query": "",  # Fix: Now initialized correctly
                })

            print(f" Sort By: {sort_by}")
            if sort_by == 'None' or sort_by ==  'playerName':
                sort_by = None
            #  Step 2: Convert AQL to SQL

            if query_type == "min":

                sql_query, count_query, selected_columns = pg_adapter.parse_min_query(
                    aql_output, 
                    team_code=team_code, 
                    count_only=False,
                    skip=(page_number - 1) * page_size, 
                    limit=page_size, 
                    filters=filters, 
                    sort_by=sort_by, 
                    sort_order=sort_order)
                
            elif query_type == "max":
                sql_query, count_query, selected_columns = pg_adapter.parse_max_query(
                    aql_output, 
                    team_code=team_code, 
                    count_only=False,
                    skip=(page_number - 1) * page_size, 
                    limit=page_size, 
                    filters=filters, 
                    sort_by=sort_by, 
                    sort_order=sort_order)
                
            elif query_type == "ltw":
                sql_query, count_query, selected_columns = pg_adapter.parse_ltw_query(
                    aql_output, 
                    team_code=team_code, 
                    count_only=False,
                    skip=(page_number - 1) * page_size, 
                    limit=page_size, 
                    filters=filters,
                    sort_by=sort_by,
                    sort_order=sort_order

                )

            elif query_type == "streak":
                sql_query, count_query, selected_columns = pg_adapter.parse_streak_query(
                    aql_output,
                    team_code=team_code,
                    count_only=False,
                    skip=(page_number - 1) * page_size,
                    limit=page_size,
                    filters=filters, 
                    sort_by=sort_by, 
                    sort_order=sort_order
                )

            else:

                sql_query, count_query, selected_columns = pg_adapter.parse_basic(
                    aql_output, 
                    team_code=team_code, 
                    count_only=False, 
                    skip=(page_number - 1) * page_size, 
                    limit=page_size, 
                    filters=filters,
                    sort_by=sort_by, 
                    sort_order=sort_order
                )

            logger.info(f" Final SQL Query:\n{sql_query}")

            logger.info(f"Generated SQL Query:\n{sql_query}")
            sql_query_output = f"SQL Query Executed at {timestamp}:\n{sql_query}"

            pg_adapter.cursor.execute(count_query)
            total_count = pg_adapter.cursor.fetchone()[0]  # Extract count result

            column_names, result_list = pg_adapter.execute_query(sql_query, selected_columns, Common.genius2athlyteshort_mapping[entity.lower()])
            logger.info(f"SQL Query Result: {result_list}")

            #  Step 4: Store results locally
            sql_output_path = os.path.join(RESULTS_DIR, f"sql_output_{timestamp}.json")
            aql_output_path = os.path.join(RESULTS_DIR, f"aql_output_{timestamp}.json")
            sql_query_log_path = os.path.join(RESULTS_DIR, f"sql_query_log_{timestamp}.txt")

            #  Save SQL execution results
            with open(sql_output_path, "w") as sql_file:
                json.dump(result_list, sql_file, indent=2)

            #  Save AQL JSON Output
            with open(aql_output_path, "w") as aql_file:
                json.dump(aql_output, aql_file, indent=2)

            #  Save SQL Query log
            with open(sql_query_log_path, "w") as sql_log_file:
                sql_log_file.write(sql_query_output)

            logger.info(f"Results stored in {RESULTS_DIR}")

        except Exception as e:
            raise e
            logger.error(f"Error processing query: {str(e)}")
            return Response({"error": f"Server Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    #  Step 5: Serialize output for Swagger UI
    output_serializer = SearchOutputSerializer(column_names=column_names, many=True)

    return Response({
        "count": total_count,
       # "results": output_serializer.data,
        "aql_output": aql_output,  #  Fix: Now initialized correctly
        "sql_query": sql_query_output,  #  Fix: Now initialized correctly
        "results": result_list,  #  Fix: Ensures valid execution results
        "positions": positions,
        "classes": player_classes,
        "teams": teams
    })


@swagger_auto_schema(
    method='post',
    operation_summary="Get Type Ahead for Team/Player Name",
    operation_description=(
        "Given a Name Prefix and whether entity is team or player, retrieve team/player name suggestions."
    ),
    manual_parameters=[
        openapi.Parameter(
            "SportCode",
            openapi.IN_QUERY,
            description="The sport code (e.g., MFB, MBB).",
            type=openapi.TYPE_STRING,
            default="MFB",
        ),
        openapi.Parameter(
            "Entity",
            openapi.IN_QUERY,
            description="The entity type (e.g., Player, Team).",
            type=openapi.TYPE_STRING,
            default="Player",
        ),
        openapi.Parameter(
            "Prefix",
            openapi.IN_QUERY,
            description="The prefix for the name.",
            type=openapi.TYPE_STRING,
            default="Tor",
        ),
    ],
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=["SportCode", "Entity", "Prefix"],
        properties={
            "SportCode": openapi.Schema(type=openapi.TYPE_STRING, example="MFB"),
            "Entity": openapi.Schema(type=openapi.TYPE_STRING, example="Player"),
            "Prefix": openapi.Schema(type=openapi.TYPE_STRING, example="Tor"),
        },
    ),
    responses={
        200: openapi.Response(
            description="The possible suggestions for name given entity and prefix",
            examples={
                "application/json": {
                    "suggestions": ["Alabama", "Arkansas"]
                }
            },
        ),
        400: openapi.Response(
            description="Invalid sport or entity.",
        ),
    },
    tags=["Search Suggestions"],
)

@api_view(['POST'])
def post_name_suggestions(request):
    '''
    {
    "SportCode": "MFB",
    "Entity": "Player",
    "Prefix": "tor"
    }
    '''
    serializer = NameSuggestionsInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    #print(validated_data)

    sport_code = validated_data.get('SportCode')
    entity = validated_data.get('Entity')
    prefix = validated_data.get('Prefix')

    try:
        suggestions = []
        if entity == "Player":
            # Case-insensitive regex search for player names starting with the prefix
            query = {
                "$or": [
                    {"playerName": {"$regex": f"^{prefix}", "$options": "i"}},  # Matches last name
                    {"firstName": {"$regex": f"^{prefix}", "$options": "i"}}   # Matches first name
                ]
            }
            results = roster_collection.find(query, {"playerName": 1, "_id": 0}).limit(10)

            suggestions = [doc["playerName"] for doc in results]
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
            return Response(
                {"error": f"No suggestions found for sportCode '{sport_code}', entity '{entity}' and prefix '{prefix}'."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"Suggestions": suggestions}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['POST'])
def report_issue(request):
    """
        Takes in all the context - query, aql and results from UI and puts it in a mongo collection.
        Also sends an email as an alert whenever user reports an issue.
    """
    request_params = json.loads(request.body)
    user_query = request_params["query"]
    sport_code = request_params["sport_code"]
    team_code = request_params["team_code"]
    entity = request_params["entity"]
    aql = request_params["aql"]
    sql = request_params["sql"]
    created_user = request_params["user"]
    created_at = datetime.now()

    doc = {
        "query": user_query,
        "sport_code": sport_code,
        "team_code": team_code,
        "entity": entity,
        "aql": aql,
        "sql": sql,
        "created_user": created_user,
        "created_at": created_at,
    }

    issue_collection.insert_one(doc)

    mail_content = f"""
    Dear Reviewer,

    {created_user} has reported an issue on {created_at}. Please find the details below:

    ---

    **🔍 Query Details:**  

    - **Query:** {user_query}  
    - **Sport Code:** {sport_code}  
    - **Team Code:** {team_code}  
    - **Entity:** {entity}  

    📌 **AQL Query:**  
    ```json
    {json.dumps(aql, indent=4)}
    ```
    📌 SQL Query:
    ```sql
    {sql}
    ```
    👤 Reported By: {created_user}
    📅 Reported At: {created_at}
    ---
    Thank you !
    """

    send_mail("Reported Issue on Athlyte R2 Search Pilot", mail_content, settings.EMAIL_HOST_USER, ["ganesh@alonzoai.in"])

    return Response({}, status=status.HTTP_200_OK)
