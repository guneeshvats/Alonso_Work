import time
from typing import List
from app.llms.openai_connector import OpenAIConnector
from app.llms.base import BaseLLMConnector
from folioprompts import Folio
from app.data_config.mappings.mappings_handler import MappingsHandler
from app.db.mongo_connection import db
import json
from jinja2 import Template
from app.constants import Qualifiers, General


class NlpProcessor:
    """
    Converts natural language queries into structured AQL using an LLM with Folio version control.
    
    This class handles the processing of natural language queries by:
    1. Converting them to AQL (Analytics Query Language) format using LLMs
    2. Managing prompt versioning through Folio
    3. Handling dynamic mappings for different sports and entities
    4. Processing team context and qualifiers
    
    Attributes:
        llm (BaseLLMConnector): LLM connector instance for query processing
        folio (Folio): Folio instance for prompt version control
        mappings_handler (MappingsHandler): Handler for loading various mappings
        team_collection: MongoDB collection for team data
        stat_matchers: Dictionary of stat matchers by sport code and entity
    """

    def __init__(self, llm: BaseLLMConnector, stat_matchers):
        """
        Initialize the NLP processor with required dependencies.

        Args:
            llm (BaseLLMConnector): LLM connector instance, defaults to OpenAI GPT-4
            stat_matchers: Dictionary mapping sport codes and entities to their respective stat matchers
        """
        self.llm = llm
        print(f"I am using LLM: {self.llm.model}")
        self.folio = Folio()
        self.mappings_handler = MappingsHandler()
        self.team_collection = db["teams"]
        self.stat_matchers = stat_matchers

    def convert_to_aql(self, basic_query: str, sport_code: str, entity: str, team_code: str, use_rag: bool = True) -> dict:
        """
        Converts a natural language query into structured AQL format using LLM processing.

        This method performs several key steps:
        1. Retrieves team context from the database
        2. Loads appropriate prompt template from Folio
        3. Dynamically loads relevant stat mappings and query samples
        4. Processes the query through LLM
        5. Parses and validates the response
        6. Ensures proper team context in qualifiers

        Args:
            basic_query (str): Natural language query to be converted
            sport_code (str): Sport identifier (e.g., "MFB" for football)
            entity (str): Query target entity type ("Player" or "Team")
            team_code (str): Team identifier code
            use_rag (bool, optional): Whether to use RAG for stat matching. Defaults to True.

        Returns:
            dict: Structured AQL containing:
                - conditions: Query conditions
                - qualifiers: Query qualifiers including team context
                - stat_period: Statistical period for the query

        Raises:
            ValueError: If team not found or if LLM response is invalid
        """
        # Fetch team name for context
        team_doc = self.team_collection.find_one({Qualifiers.TEAM_CODE.value: str(team_code)})
        if not team_doc or Qualifiers.TEAM_NAME.value not in team_doc:
            raise ValueError(f"No team found for teamCode: {team_code}")

        team_name = team_doc[Qualifiers.TEAM_NAME.value]

        context = {Qualifiers.TEAM_NAME.value: team_name}

        # Step 1: Load the latest prompt version from Folio
        prompt_entry = self.folio.get_prompt("nlp_query_conversion")
        if not prompt_entry:
            raise ValueError("Prompt 'nlp_query_conversion' is missing from Folio. Please add it.")

        print(sport_code, entity, team_code)
        selected_stat_matcher = self.stat_matchers[sport_code][entity]
        # Step 2: Load stat mapping and query samples dynamically
        if use_rag:
            s = time.time()
            stat_mapping = selected_stat_matcher.match(basic_query)
            print("[DEBUG] Raw stat_mapping from match():", json.dumps(stat_mapping, indent=2))
            e = time.time()
            print(f"Took {e - s:.2f} seconds to load {len(stat_mapping)} stats")
            print("Stat Mapping ::",stat_mapping)
        else:
            stat_mapping = self.mappings_handler.get_stat_mapping(sport_code, entity)

        stat_mapping = [
            {
                "stat": x["stat"],
                "full_name": x["name"],
                "description": x["description"],
                "category": x.get("category", "Unknown"),
                "aliases": x.get("aliases", []),
                "sub_category": x.get("sub_category", "")
            }
            for x in stat_mapping
        ]

        query_samples = self.mappings_handler.get_query_samples(sport_code, entity)
        pos_mapping = self.mappings_handler.get_pos_mapping(sport_code)

        template = Template(prompt_entry.text)

        # Step 3: Format the prompt dynamically
        formatted_prompt = template.render(
            natural_language_query=basic_query,
            sport_code=sport_code,
            entity=entity,
            context=context,
            stat_mapping=json.dumps(stat_mapping, indent=2),
            query_samples=query_samples,
            pos_mapping=json.dumps(pos_mapping, indent=2)
        )

        ##### DEBUG STATEMENT !!!
        print("Formatted Prompt:\n", formatted_prompt)

        # Step 4: Get AQL response from LLM
        s = time.time()
        aql_response = self.llm.generate_response(
            formatted_prompt  #, response_format="json"  # Ensure LLM returns JSON
        )
        e = time.time()
        print(f"AQL Generation took {e - s:.2f} seconds")
        # Debug: Print response
        print("Raw LLM Response:\n", repr(aql_response))  # Use repr() to see if response is empty or malformed

        # Step 6: Parse response safely
        try:
            if isinstance(aql_response, dict):
                return aql_response  #  Already a dict, return as-is

            aql_response = aql_response.strip("`json\n").strip("`")  # Remove any markdown
            aql_response = json.loads(aql_response)  #  Parse cleaned JSON string
            #  Ensure 'qualifiers' exists and is a dict
            if 'qualifiers' not in aql_response or not isinstance(aql_response['qualifiers'], dict):
                aql_response['qualifiers'] = {}

            # if Qualifiers.TEAM_NAME.value not in aql_response['qualifiers']:
            #     if (Qualifiers.OPPONENT_TEAM_NAME.value not in aql_response['qualifiers']) or (aql_response['qualifiers'][Qualifiers.OPPONENT_TEAM_NAME.value]
            #             != team_name):
            #         aql_response['qualifiers'][Qualifiers.TEAM_NAME.value] = team_name
            return aql_response

        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON received from LLM:\n{repr(aql_response)}")