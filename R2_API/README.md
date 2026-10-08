# R2_API

Link to the documentation - [Link](https://docs.google.com/document/d/1ZR0fZWEQ1_IvaeHs8bzfwZIdw1IMZRJNBYma6dQjCVU/edit?usp=sharing)

## Setting up the environment 

```
conda create --name <environment_name> python=3.10.16
conda activate <environment_name>
```

```
pip install -r requirements.txt
```


## Command to run 
`cd R2_API`
```
uvicorn main:app --reload 
```

## Updating Prompts with Folio

To update the NLP query conversion prompt through Folio:

1. Navigate to the root directory containing the Folio folder
2. Run the following command:
```
cat folio/prompts/nlp_query_conversion/latest| folio add nlp_query_conversion
```

## Payload Request to /api/search
Example
```
{
  "BasicQuery": "players having atleast 1+ total points scored",
  "SportCode" : "MFB",
  "TeamCode": "31",
  "AQLOnly": false,
  "Entity": "Player",
  "TimePeriod": "Game",
  "GamePeriod": "All Quarters",
  "PageNumber": 1,
  "PageSize": 10,
  "Filters": {},
  "Llm": "openai",
  "LlmModel": "gpt-4o",
  "UseRAG": true
}
```
Response Structure 
```
{
  "results": [
    {
      "metadata": {
        "ID": 1,
        "TEAM": "Alabama",
        "PLAYER": "Marshawn Powell",
              .
              . 
      },
      "stats": {
        "FGMADE": 
      }
    }
  ],
  "total": 1
}

 "aql_output": {
    "query_type": "streak",
    "conditions": "sFieldGoalsMade >= 1",
    "qualifiers": {
      "teamName": "Arkansas"       
    },
    "stat_period": "game",
    "streak_len": null
  },
  "Sql_query": “"SELECT ROW_NUMBER() OVER () AS id, playername, gameresult, gamedate, position, sFieldGoalsMade, opponentteamname, teamname, playerclass
  FROM player_game_statistics
  WHERE sFieldGoalsMade >= 1 AND teamName = 'Arkansas'\nORDER BY sFieldGoalsMade DESC\nLIMIT 10 OFFSET 0;”

 "inference_time": (in s),
 
  "positions": [
    Based on the sport_code and the query-qualifiers
  ],

  "classes": null,

  "teams": []

```

## Directory Structure 
```
R2_API/
│-- app/
│   │-- api/
│   │   │-- routes/
│   │   │   │-- search.py  # Search API endpoint (/api/search)
│   │   │   │-- report.py  # Issue reporting API endpoint (/report)         [NOT IMPLEMENTED YET]
│   │   │   │-- auth.py  # User Authentication endpoint (/auth/register, /auth/login, /auth/refresh)
│   │-- services/
│   │   │-- nlp_processor.py  # Handles NLP query processing (AQL Extraction from NL query)
│   │   │-- sql_builder.py  # AQL to SQL conversion logic (Generates appropriate SQL from the structured AQL data)
│   │   │-- email_service.py  # Email notifications        [NOT IMPLEMENTED YET]
│   │   │-- stat_matcher.py  # Encodings model (RAG for shortlisting the stat_mappings)
│   │-- db/
│   │   │-- pgsql_adapter.py  # PostgreSQL interactions (Implements the generated SQL query in postgres & returns the results)
│   │   │-- mongodb_connection.py  # Mongo Credentials and setsup the db
│   │-- models/
│   │   │-- search_models.py  # Pydantic models for search API
│   │   │-- report_models.py  # Pydantic models for issue reporting
│   │-- llms/
│   │   │-- __init__.py  # LLM Enums and Connector class
│   │   │-- base.py  # Base LLM handling class
│   │   │-- openai_connector.py  # OpenAI models integration
│   │   │-- gemini_connector.py  # Gemini models integration
│   │   │-- groq_connector.py  # Groq models integration
│   │-- ml_assets/
│   │   │-- MFB/
│   │   │   │-- Player.index
│   │   │   │-- Team.index  
│   │   │-- MBB/
│   │   │   │-- Player.index
│   │   │   │-- Team.index  
│   │-- docs/  
│   │   │-- generate_docs.py  # Auto-generate documentation (in .md format for a specific script or all scripts of project)
│   │   │-- README.md  # Project overview and setup guide
│   │   │-- documentation/
│   │   │   │-- ### All the documentations created using generate_docs.py will be stored here
│   │-- data_config/
│   │   │-- mappings/
│   │   │   │-- __init__.py  
│   │   │   │-- table_mapping.json  # Table Name Depends on --> (sport_code, entity, stat_period)
│   │   │   │-- mappings_handler.py  # Handles the fetching of various mappings throuhghout the project
│   │   │   │-- metadata_mapping.json # For metadata keys displayed in final response (Same for both MBB and MFB) 
│   │   │   │-- pos_mapping.json  # (depends on sport_code)
│   │   │   │-- filters_mapping.json  # (static mapping used in sql_builder.py script) 
│   │   │   │-- fields_mapping.json  # Fields/Columns displayed depends on --> (sport_code, entity, stat_period, query_type)
│   │   │   │-- stat_mapping/
│   │   │   │   │-- MFB/
│   │   │   │   │   │-- Player.json  # Stat mapping for Player queries of MFB
│   │   │   │   │   │-- Team.json    # Stat mapping for Team queries of MFB
│   │   │   │   │-- MBB/
│   │   │   │   │   │-- Player.json  # Stat mapping for Player queries of MBB
│   │   │   │   │   │-- Team.json    # Stat mapping for Team queries of MBB
│   │   │-- query_samples/     # query examples passed to prompt --> depends on (sport_code, Entity)
│   │   │   │-- MFB/
│   │   │   │   │-- Player.json  # Example queries for player queries (passed to prompt) 
│   │   │   │   │-- Team.json  # Example queries for team queries (passed to prompt)
│   │   │   │-- MBB/
│   │   │   │   │-- Player.json  # Example queries for player queries (passed to prompt) 
│   │   │   │   │-- Team.json  # Example queries for team queries (passed to prompt)
│   │-- sql_templates.py/  
│   │   │-- sql_template_loader.py  # Class to load the SQL templates anywhere in the project
│   │   │-- basic.sql  # query_type = basic SQL query template
│   │   │-- max.sql  # query_type = max SQL query template
│   │   │-- min.sql  # query_type = min SQL query template
│   │   │-- ltw.sql  # query_type = ltw SQL query template
│   │   │-- streak.sql  # streak SQL query template [OBSOLETE]
│   │   │-- streak_mfb_player.sql  # query_type = "streak" SQL query template for sport_code = "MFB" and Entity = "Player"
│   │   │-- streak_mfb_team.sql  # query_type = "streak" SQL query template for sport_code = "MFB" and Entity = "Team"
│   │   │-- streak_mbb_player.sql  # query_type = "streak" SQL query template for sport_code = "MBB" and Entity = "Player" 
│   │   │-- streak_mbb_team.sql  # query_type = "streak" SQL query template for sport_code = "MBB" and Entity = "Team"
│   │-- folio/
│   │   │-- prompts/
│   │   │   │-- 1  # Prompt Version 1
│   │   │   │-- 2  # Prompt Version 2
│   │   │   │-- 3  # Prompt Version 3 (There will be many more versions as we update it)
│   │   │   │-- latest  # Latest version where changes are made
│   │-- .github/
│   │   │-- workflows/
│   │   │   │-- deploy.yml   # Essential for CI/CD Pipeline 
│   │-- tests/
│   │   │-- app/
│   │   │   │-- api/
│   │   │   │   │-- routes/
│   │   │   │   │   │-- test_search.py  
│   │   │   │   │   │-- test_auth.py  
│   │   │   │-- services/
│   │   │   │   │-- test_sql_builder.py
│   │   │   │   │-- test_nlp_processor.py
│   │   │   │   │-- test_stat_matcher.py
│   │   │   │-- db/
│   │   │   │   │-- test_pgsql_adapter.py  
│   │   │   │   │-- test_mongodb_connection.py  
│   │   │   │-- data_config/
│   │   │   │   │-- mappings_handler.py  
│   │   │-- conftest.py  # This contains the general path importing for tests folder
│-- .env  # Environment variables
│-- .gitignore  # Environment variables
│-- requirements.txt  # Python dependencies
│-- main.py  # FastAPI entry point
│-- README.md  # Readme file of the whole project
```

## When you update the stat mappings run this command:
Replace the paths with corresponding `sport_code` and `enitity` index file and json file.
Sample of the command
```
python app/services/stat_matcher.py create /Users/guneeshvats/Desktop/Alonso_Work/R2_API/app/data_config/mappings/stat_mapping/MBB/Team.json /Users/guneeshvats/Desktop/Alonso_Work/R2_API/app/ml_assets/MBB/Team.index
```