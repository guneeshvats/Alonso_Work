import json
import random
import wandb
import requests
import time
import os
import typer
import re
import uuid
import logging
from rich import print
from rich.progress import track

#  Define file paths
#NL_SEARCH_API_URL = "https://dev-r2.athlytesports.com/api/search/"
#AUTH_URL = "https://dev-r2.athlytesports.com/auth/login"
NL_SEARCH_API_URL = "http://localhost:8000/api/search/"
AUTH_URL = "http://localhost:8000/auth/login"

logger = logging.getLogger(__name__)

def load_ground_truth(file_path):
    """Loads ground truth data from a JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


# Authenticate and get token
def get_auth_token(username, password):
    """Authenticates the user and retrieves the JWT token."""
    payload = {
        "username": username,
        "password": password
    }
    response = requests.post(AUTH_URL, data=payload)

    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"Authentication successful! Token: {token[:20]}...")  # Print partial token for debugging
        return token
    else:
        print(f"Authentication Failed: {response.json()}")
        return None



def call_nl_search(query, entity, time_period, llm, llm_model, use_rag, token, sport_code):
    """Calls the NL Search API and extracts AQL response."""
    payload = {
        "BasicQuery": query,
        "SportCode": sport_code,  # Dynamic Sport Code
        "Entity": entity.title(),
        "TimePeriod": time_period,
        "TeamCode" : "31",
        "AQLOnly" : True, 
        "GamePeriod": "All Quarters",
        "PageNumber": 1,
        "PageSize": 10,
        "SortBy": "PLAYER",
        "SortOrder": "ASC",
        "Llm": llm,
        "LlmModel": llm_model,
        "UseRAG" : use_rag
    }
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(NL_SEARCH_API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            response_json = response.json()
            return extract_aql(response_json)
        else:
            print(f" Failed for query: {query}, Status Code: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        print(f"⚠️ Error calling API for query: {query}, Error: {e}")
        return None


def extract_aql(response_data):
    """Extracts AQL output from API response."""
    return {
        "query_type": response_data.get("aql_output", {}).get("query_type", "basic"),
        "entity": response_data.get("entity", "player").lower(),
        "qualifiers": response_data.get("aql_output", {}).get("qualifiers", {}),
        "stat_period": response_data.get("aql_output", {}).get("stat_period", "").lower(),
        "conditions": response_data.get("aql_output", {}).get("conditions", "").lower(),
        "inference_time" : response_data.get("inference_time")
    }


def convert_conditions_to_lowercase(conditions):
    """Converts condition field names to lowercase."""
    if not conditions:
        return ""
    return re.sub(r'\"([^\"]+)\"', lambda m: f'"{m.group(1).lower()}"', conditions.lower())


def compare_qualifiers(predicted, expected):
    """Compares qualifiers by converting all values to lowercase."""
    if not predicted or not expected:
        return predicted == expected  #  Handles empty cases

    # Convert all values in the dictionaries to lowercase
    def lowercase_values(d):
        if isinstance(d, dict):
            return {k.lower(): lowercase_values(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [str(v).lower() for v in d]
        else:
            return str(d).lower()

    return lowercase_values(predicted) == lowercase_values(expected)


def compare_conditions(predicted, expected):
    """Compares conditions (ignores case & whitespace)."""
    return predicted.strip().lower() == expected.strip().lower()


def compute_accuracy(results):
    """Computes accuracy scores."""
    total = len(results)
    if total == 0:
        return {
            "accuracy_qualifiers": 0, 
            "accuracy_conditions": 0, 
            "accuracy_stat_period": 0, 
            "accuracy_query_type": 0, 
            }

    correct_qualifiers = sum(1 for r in results if r["flag_qualifiers"])
    correct_conditions = sum(1 for r in results if r["flag_conditions"])
    correct_stat_period = sum(1 for r in results if r["flag_stat_period"])
    correct_query_type = sum(1 for r in results if r["flag_query_type"])  
    

    return {
        "accuracy_qualifiers": round((correct_qualifiers / total) * 100, 2),
        "accuracy_conditions": round((correct_conditions / total) * 100, 2),
        "accuracy_stat_period": round((correct_stat_period / total) * 100, 2),
        "accuracy_query_type": round((correct_query_type / total) * 100, 2)
    }


app = typer.Typer()


def run_sample(gt_item, llm, llm_model, use_rag, token, sport_code):
    query = gt_item["query"]
    entity = gt_item["entity"]
    expected_aql = gt_item["aql"]

    predicted_aql = call_nl_search(query, entity, expected_aql["stat_period"], llm, llm_model, use_rag, token, sport_code)
    results = {}
    if predicted_aql:

        predicted_conditions = convert_conditions_to_lowercase(predicted_aql["conditions"])
        expected_conditions = convert_conditions_to_lowercase(expected_aql["conditions"])
        flag_conditions = compare_conditions(predicted_conditions, expected_conditions)

        flag_qualifiers = compare_qualifiers(predicted_aql["qualifiers"], expected_aql["qualifiers"])
        flag_stat_period = predicted_aql["stat_period"] == expected_aql["stat_period"]
        flag_query_type = predicted_aql["query_type"] == expected_aql["query_type"]


        results = {
                "query": query,
                "ground_truth_aql": expected_aql,
                "predicted_aql": predicted_aql,
                "flag_qualifiers": flag_qualifiers,
                "flag_conditions": flag_conditions,
                "flag_stat_period": flag_stat_period,
                "flag_query_type" : flag_query_type,
                "inference_time": predicted_aql["inference_time"]
        }

    return results


def make_output_dir(root_dir):
    random_string = uuid.uuid4().hex
    target_dir = os.path.join(root_dir, random_string)
    os.mkdir(target_dir)
    return target_dir


@app.command()
def run(ground_truth_file: str = typer.Argument(help="JSON file containing ground truth data"),
        num_samples: int = typer.Option(default=0, help="Number of samples to run"),
        randomize: bool = typer.Option(default=False, help="Whether to randomize the samples"),
        outputs_dir=typer.Option(default="test_outputs", help="Output directory"),
        llm = typer.Option(default="openai", help="Choose the LLM service"),
        llm_model = typer.Option(default="gpt-4o", help="Choose the LLM Model"),
        use_rag: bool = typer.Option(default=False, help="Whether to use RAG to shortlist stats"),
        username: str = typer.Option(..., help="Username for authentication"),
        password: str = typer.Option(..., help="Password for authentication"),
        sport_code: str = typer.Option(..., help="Sport code (e.g., MFB, MBB, etc.)")    
    ):


    wandb.init(
        # set the wandb entity where your project will be logged (generally your team name)
        entity="neshkatrapati-alonzo-ai",

        # set the wandb project where this run will be logged
        project="nl_query_testing",

        # track hyperparameters and run metadata
        config={
            "ground_truth_file": ground_truth_file,
            "num_samples": num_samples,
            "randomize": randomize,
            "outputs_dir": outputs_dir,
            "entity" : "player",
            "stat_scope" : "R1",
            "llm" : llm,
            "llm_model" : llm_model,
            "use_rag" : use_rag,
            "sport_code" : sport_code
        }
    )

    # Authenticate and get token
    token = get_auth_token(username, password)
    if not token:
        print("Exiting due to authentication failure.")
        return

    ground_truth_data = load_ground_truth(ground_truth_file)
    target_dir = make_output_dir(outputs_dir)
    print(f"Starting test run. Output directory: [bold] {target_dir} [/bold] :white_heavy_check_mark: ")

    log_file = os.path.join(target_dir, "log.txt")
    logging.basicConfig(filename=log_file, encoding='utf-8', level=logging.DEBUG)
    logger.info(f"Running {num_samples} samples from {ground_truth_file}")

    num_samples = num_samples if num_samples > 0 else len(ground_truth_data)
    all_results = []
    for i in track(range(num_samples), description = "Gathering Results..."):
        sample_id = i
        if randomize:
            sample_id = random.randint(0, num_samples)

        sample = ground_truth_data[sample_id]
        logger.info(f"Sample ID: {sample_id}")
        logger.info(f"Sample: {json.dumps(sample, indent=2)}")

        results = run_sample(sample, llm, llm_model, use_rag, token, sport_code)
        if results:
            all_results.append(results)
            tbl = wandb.Table(columns=list(results.keys()))
            tbl.add_data(*results.values())
            wandb.log({"inference_time": results["inference_time"]})
            wandb.log({"predictions" : tbl})

    with open(os.path.join(target_dir, "all_results.json"), "w") as f:
        json.dump(all_results, f, indent=4)

    accuracy_scores = compute_accuracy(all_results)
    wandb.log(accuracy_scores)
    print(f"Accuracy scores for {num_samples} samples: {accuracy_scores}")
    print(f"Output has been saved to {os.path.join(target_dir, 'all_results.json')}")
    wandb.finish()




if __name__ == "__main__":

    
    app()

    #
    # #  Compute and print accuracy scores
    # accuracy_scores = compute_accuracy(results)
    # print("\n🎯 Accuracy Scores:")
    # print(json.dumps(accuracy_scores, indent=4))
