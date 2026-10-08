from openai import OpenAI, RateLimitError
from pymongo import MongoClient
from decouple import config
import json
import backoff
import time
import traceback
import logging
import re

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
                
        chatgpt_request = [
                {"role": "system", "content": "You are an assistant that converts natural language queries to MongoDB find parameters."},
                {"role": "user", "content": prompt}
            ]
        #model = "gpt-4o-mini"
        model = "gpt-4o"

        try:
            response = self.completions_with_backoff(model,chatgpt_request)
            self.logger.debug(f"API response headers: {response.headers}")
            response = response.parse()

            tweets = []
            if response:
                r_usage = response.usage
                self.logger.debug(f"Response usage: {r_usage}")
                raw_content = response.choices[0].message.content.strip()
                print("RAW content: ", raw_content)
                try:
                    # Attempt to parse the response as JSON
                    return json.loads(raw_content)
                except json.JSONDecodeError as json_error:
                    print(f"JSON parsing error: {json_error}")
                    print("Attempting to recover...")
                    # Manual adjustment: Remove extra newlines and whitespace
                    cleaned_content = raw_content.replace("\n", "").replace("/_", "_").strip()
                    cleaned_content = re.sub(r"```(json)?", "", cleaned_content).strip()
                    print("cleaned_content: ", cleaned_content)
                    try:
                        return json.loads(cleaned_content)
                    except json.JSONDecodeError:
                        print("Failed to recover valid JSON.")
                        return {"mongo_find_params": {}}

        except Exception as e:
            self.logger.error(f"Error generating response from OpenAI: {e}")
            self.logger.error("Stack Trace: " + traceback.format_exc())

        return {"mongo_find_params": {}}
    
    def generate_search_queries(self, natural_language_query, stat_mapping=default_stat_mapping):
        """
        Generates MongoDB query parameters from a natural language query using OpenAI's GPT model.

        :param natural_language_query: str, the natural language query.
        :param stat_mapping: dict, a mapping of natural language terms to database column names.
        :return: dict, the MongoDB query parameters.
        """
        # Prepare the prompt for GPT
        prompt = f"""
        Convert the following natural language query into MongoDB find parameters using the provided stat mapping.

        ## Instructions:
        - **Ensure that all values in the output strictly come from the values in the provided stat mapping.**
        - **Match query terms to the closest key in stat mapping if an exact match is not found.**
        - **Do not introduce any values that are not in the stat mapping.**
        - Use the best possible match when multiple similar keys exist.
        - Convert comparative conditions (e.g., "over 25", "greater than 20") into MongoDB operators (`$gt`, `$gte`, `$lt`, `$lte`).
        - The output must strictly follow the JSON format below. **Only return the expected output. No other text.**

        ## Query:
        "{natural_language_query}"

        ## Stat Mapping:
        {json.dumps(stat_mapping, indent=2)}

        ## Expected Output (Strict JSON Format):
        {{
        "mongo_find_params": {{}}
        }}

        Make sure:
        1. The **values** in the output strictly follow the stat mapping.
        2. If no exact key match exists, find the **closest key**.
        3. Avoid using any undefined terms.
        """

        mongo_query = self.get_openai_response(prompt)

        return mongo_query['mongo_find_params']


    
def get_stat_mapping(entity):
    stat_mapping_query = {"entity":entity.lower()}
    stat_mapping_ag = {entry['AthlyteLabel']: entry['GeniusLabel'] for entry in statmapping_collection.find(stat_mapping_query)}
    return stat_mapping_ag



# Example usage
if __name__ == "__main__":
    entity = "player"
    stat_mapping = get_stat_mapping(entity)
    natural_language_query = "rushing yards over 25 and receiving yards greater than 20"
    #result = generate_mongo_query(natural_language_query, stat_mapping)

    nlp_search = NlpSearch(logger)
    nlp_search_query = nlp_search.generate_search_queries(natural_language_query, stat_mapping)
    print("OP: ", nlp_search_query)



'''

def generate_mongo_query(natural_language_query, stat_mapping=default_stat_mapping):
    """
    Generates MongoDB query parameters from a natural language query using OpenAI's GPT model.

    :param natural_language_query: str, the natural language query.
    :param stat_mapping: dict, a mapping of natural language terms to database column names.
    :return: dict, the MongoDB query parameters.
    """
    # Prepare the prompt for GPT
    prompt = f"""
    Convert the following natural language query into MongoDB find parameters.

    Query: "{natural_language_query}"

    Stat mapping:
    {json.dumps(stat_mapping, indent=2)}

    Output only in JSON format strictly as:
    {{
      "mongo_find_params": {{}}
    }}
    """

    # Call OpenAI's API
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an assistant that converts natural language queries to MongoDB find parameters."},
                {"role": "user", "content": prompt}
            ]
        )

        # Log raw API response for debugging
        #print("Raw API response:", response)

        # Extract the response content
        raw_content = response.choices[0].message.content.strip()
        #print("Raw Content:", raw_content)

        # Clean up and validate the JSON output
        try:
            # Attempt to parse the response as JSON
            return json.loads(raw_content)
        except json.JSONDecodeError as json_error:
            print(f"JSON parsing error: {json_error}")
            print("Attempting to recover...")
            # Manual adjustment: Remove extra newlines and whitespace
            cleaned_content = raw_content.replace("\n", "").strip()
            try:
                return json.loads(cleaned_content)
            except json.JSONDecodeError:
                print("Failed to recover valid JSON.")
                return {"mongo_find_params": {}}

    except Exception as e:
        print(f"Error: {e}")
        return {"mongo_find_params": {}}
'''