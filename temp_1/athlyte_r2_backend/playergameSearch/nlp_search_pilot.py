from openai import OpenAI, RateLimitError
from pymongo import MongoClient
from decouple import config
from datetime import datetime
import json
import backoff
import time
import traceback
import logging
import re
import pandas as pd
from folioprompts import Folio
from jinja2 import Template
from playergameSearch.nlp_pilot_test_queries import nl_queries
# from nlp_pilot_test_queries import nl_queries

rate_limit_per_minute = 1000
delay = 60.0/rate_limit_per_minute

# Initialize the OpenAI client
openai_api_key = config('OPENAI_API_KEY')

# Get MongoDB connection string from environment variables
mongo_uri = config('DB_URI')
db_name = config('DB_NAME')

# Connect to MongoDB using PyMongo
client = MongoClient(mongo_uri)
db = client[db_name]
playergame_collection = db['PlayerGameStatistics']
statmapping_collection = db['stat_mapping']

# Example stat mapping
default_stat_mapping = {
    "Rushing yards net": "sRushingYardsNet",
    "Reception yards": "sReceptionsYards",
}

logging.basicConfig(
    level=logging.INFO,  # You can set this to DEBUG for more detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger()

class NlpSearch:
    def __init__(self, logger):
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.logger = logger
        self.folio = Folio.init()  #  Initialize Folio

        # Load Stat Mapping
        self.stat_mapping = self.load_stat_mapping("playergameSearch/stat_mapping.json")

        # Load Position Mapping
        self.pos_mapping = self.load_mapping("playergameSearch/pos_mapping.json")

    
    def load_stat_mapping(self, file_path):
        """
        Loads stat mapping from a JSON file and extracts only 'stat' and 'description' fields.
        
        Returns:
            dict: {stat: description} mapping.
        """
        try:
            df = pd.read_json(file_path)  # Load JSON as Pandas DataFrame
            stat_mapping = dict(zip(df["stat"], df["description"]))  # Convert to dict
            return stat_mapping
        except Exception as e:
            self.logger.error(f"Error loading stat mapping file: {e}")
            return {}

    def load_mapping(self, file_path):
        """
        Loads a mapping from a JSON file.

        Args:
            file_path (str): Path to JSON file.

        Returns:
            dict: Loaded mapping.
        """
        try:
            with open(file_path, "r") as file:
                return json.load(file)
        except Exception as e:
            self.logger.error(f"Error loading mapping file {file_path}: {e}")
            return {}

    @backoff.on_exception(backoff.expo, RateLimitError)
    def completions_with_backoff(self,model,messages,temperature=0.1):
        try:
            self.logger.debug("Making request to OpenAI API with backoff.")
            response = self.openai_client.chat.completions.with_raw_response.create(
                model=model,
                messages=messages,
                temperature=temperature
            )
            return response
        except RateLimitError as e:
            self.logger.warning(f"Rate limit error: {e}. Retrying with backoff...")
            raise

    def get_openai_response(self, prompt):
        print(prompt)
        chatgpt_request = [
            {"role": "system", "content": "You are an assistant that converts natural language queries to structured AQL."},
            {"role": "user", "content": prompt}
        ]
        model = "gpt-4o"

        try:
            response = self.completions_with_backoff(model, chatgpt_request)
            self.logger.debug(f"API response headers: {response.headers}")
            response = response.parse()

            if response:
                r_usage = response.usage
                self.logger.debug(f"Response usage: {r_usage}")
                raw_content = response.choices[0].message.content.strip()

                try:
                    return json.loads(raw_content)
                except json.JSONDecodeError:
                    cleaned_content = re.sub(r"```(json)?", "", raw_content).strip()
                    try:
                        return json.loads(cleaned_content)
                    except json.JSONDecodeError:
                        self.logger.error("Failed to recover valid JSON.")
                        return {"conditions": "", "stat_period": "game", "qualifiers": {}, "query_type": "basic"}

        except Exception as e:
            self.logger.error(f"Error generating response from OpenAI: {e}")
            self.logger.error("Stack Trace: " + traceback.format_exc())

        return {"conditions": "", "stat_period": "game", "qualifiers": {}, "query_type": "basic"}

    
    def generate_search_queries(self, natural_language_query, context = {}):
        """
        Generates MongoDB query parameters from a natural language query using OpenAI's GPT model.

        :param natural_language_query: str, the natural language query.
        :param stat_mapping: dict, a mapping of natural language terms to database column names.
        :return: dict, the MongoDB query parameters.
        """

        #  Load previous prompt version if exists, otherwise create a new entry
        prompt_entry = self.folio.get_prompt("nlp_query_conversion")

        if not prompt_entry:
            raise ValueError("Prompt 'nlp_query_conversion' is missing from Folio. Please add it.")

            # Render the prompt dynamically
        #  Render the prompt dynamically
        template = Template(prompt_entry.text)
        rendered_prompt = template.render(
            natural_language_query=natural_language_query, 
            stat_mapping=json.dumps(self.stat_mapping, indent=2),
            position_mapping=json.dumps(self.pos_mapping, indent=2),
            context=context
        )
        print(rendered_prompt)

        #  Get OpenAI Response
        mongo_query = self.get_openai_response(rendered_prompt)

        #  Extract values
        conditions = mongo_query.get("conditions", "")
        stat_period = mongo_query.get("stat_period", "game")  
        qualifiers = mongo_query.get("qualifiers", {})
        query_type = mongo_query.get("query_type", "basic")  # Extracting query type
        streak_len = mongo_query.get("streak_len", None) # Extract streak length if applicable and default value is None
        valid_types = {"basic", "min", "max", "ltw", "streak"}
        if query_type not in valid_types:
            query_type = "basic"  # Fallback if invalid

        #  Remove empty fields from qualifiers
        qualifiers = {k: v for k, v in qualifiers.items() if v}

        return conditions, stat_period, qualifiers, query_type, streak_len


def get_stat_mapping(entity):
    stat_mapping_query = {"entity":entity.lower(), "R1":True}
    # stat_mapping_ag = {entry['AthlyteLabel'].lower(): entry['Description'] for entry in statmapping_collection.find(stat_mapping_query)}
    stat_mapping_ag = {entry['GeniusLabel']: entry['Description'] for entry in statmapping_collection.find(stat_mapping_query)}
    return stat_mapping_ag

def normalize_query(query):
    """Extracts conditions as a sorted list to compare structure."""
    # Remove escape characters and extra spaces
    query = re.sub(r'\s+', ' ', query.strip().replace('\\"', '"'))
    # Split conditions by logical operators (AND/OR) while preserving them
    conditions = re.split(r'\s+(AND|OR)\s+', query)
    # Sort conditions while keeping AND/OR in place
    sorted_conditions = sorted(conditions, key=lambda x: x.strip() if x not in {"AND", "OR"} else "")
    return sorted_conditions


def extract_conditions(condition_str):
    # Extract stat names (inside double quotes) and logical operators (AND/OR)
    stat_names = re.findall(r'"(.*?)"', condition_str)
    logical_operators = re.findall(r'\b(AND|OR)\b', condition_str)
    
    # Tokenize input while preserving operators
    tokens = re.split(r'(\bAND\b|\bOR\b|".*?")', condition_str)
    tokens = [token.strip() for token in tokens if token.strip()]
    
    # Interleave stat names and logical operators
    combined_list = []
    for token in tokens:
        if token in {"AND", "OR"}:
            combined_list.append(token)
        elif token.startswith('"') and token.endswith('"'):
            combined_list.append(token.strip('"').lower())
    
    return combined_list

def compare_op(op, expected_op):
    # Ensure exact match for query_type, entity, qualifier, and stat_period
    if (op["query_type"] != expected_op["query_type"] or
        op["entity"] != expected_op["entity"] or
        op["qualifier"] != expected_op["qualifier"] or
        op["stat_period"] != expected_op["stat_period"]):
        return False
    
    # Extract and compare stat conditions
    op_stat = extract_conditions(op["conditions"].lower())
    eo_stat = extract_conditions(expected_op["conditions"].lower())
    
    # Add extracted conditions to the dictionaries for reference
    op["op_stat"] = op_stat
    expected_op["eo_stat"] = eo_stat
    
    return op_stat == eo_stat



# Example usage
if __name__ == "__main__":
    #entity = "team"
    query_type = "Basic"
    entity = "player"
    stat_mapping = get_stat_mapping(entity)
    query = "rushing yards over 250 and receiving yards greater than 200 in a season"

    nlp_search = NlpSearch(logger)
    matches_count= 0
    total_count = 0

    with open(f"pilot_q1_output_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt", "w") as file:
        for nl_query in nl_queries:
            nlp_search_query, stat_period = nlp_search.generate_search_queries(nl_query['query'], stat_mapping)
            op = {
                "query_type": query_type,
                "entity": entity,
                "qualifier": {},
                "stat_period": stat_period,
                "conditions": nlp_search_query
            }
            #print(op)
            expected_op = nl_query['op']
            #expected_op["conditions"] = normalize_query(expected_op["conditions"])
            matches = False
            if compare_op(op, expected_op):
                matches = True
                matches_count += 1
            total_count += 1
            file.write(f"Entity: {entity}\nQuery: {nl_query['query']}\nOp: {op}\nEO: {expected_op}\nMatches:{matches}\n\n")
        accuracy = (matches_count / total_count) * 100
        file.write(f"Accuracy for gpt is {accuracy}. Matches_count: {matches_count}. Total_count: {total_count}")
        
    
