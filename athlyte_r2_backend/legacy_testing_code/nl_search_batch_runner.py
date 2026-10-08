import json
import requests
import time
import os
import re 

#  Define file paths
GROUND_TRUTH_FILE = "ground_truth_with_qualifiers.json"
OUTPUT_FILE = "merged_json_qualifiers.json"
NL_SEARCH_API_URL = "http://127.0.0.1:8000/search_nl/"  # Change if needed

def load_ground_truth(file_path):
    """Loads ground truth data from a JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)

def call_nl_search(query, entity, time_period):
    """Calls the NL Search API and extracts AQL response."""
    payload = {
        "BasicQuery": query,
        "SportCode": "MFB",  #  Fixed Sport Code
        "Entity": entity,
        "TimePeriod": time_period,
        "GamePeriod": "All Quarters",
        "PageNumber": 1,
        "PageSize": 10,
        "SortBy": "PLAYER",
        "SortOrder": "ASC"
    }

    try:
        response = requests.post(NL_SEARCH_API_URL, json=payload)
        if response.status_code == 200:
            response_json = response.json()
            return extract_aql(response_json)
        else:
            print(f"❌ Failed for query: {query}, Status Code: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        print(f"⚠️ Error calling API for query: {query}, Error: {e}")
        return None

def extract_aql(response_data):
    """Extracts AQL output from API response."""
    return {
        "query_type": "basic",  #  Hardcoded to 'basic'
        "entity": response_data.get("entity", "").lower(),
        "qualifiers": response_data.get("aql_output", {}).get("qualifier", {}),
        "stat_period": response_data.get("aql_output", {}).get("stat_period", "").lower(),
        "conditions": response_data.get("aql_output", {}).get("conditions", "").lower()
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
        return {"accuracy_qualifiers": 0, "accuracy_conditions": 0, "accuracy_stat_period": 0}

    correct_qualifiers = sum(1 for r in results if r["flag_qualifiers"])
    correct_conditions = sum(1 for r in results if r["flag_conditions"])
    correct_stat_period = sum(1 for r in results if r["flag_stat_period"])

    return {
        "accuracy_qualifiers": round((correct_qualifiers / total) * 100, 2),
        "accuracy_conditions": round((correct_conditions / total) * 100, 2),
        "accuracy_stat_period": round((correct_stat_period / total) * 100, 2)
    }

if __name__ == "__main__":
    ground_truth_data = load_ground_truth(GROUND_TRUTH_FILE)
    results = []

    for item in ground_truth_data:
        query = item["query"]
        entity = item["entity"]
        expected_aql = item["aql"]

        print(f"🚀 Processing: {query}")
        predicted_aql = call_nl_search(query, entity, expected_aql["stat_period"])

        if predicted_aql:
            # flag_qualifiers = compare_qualifiers(predicted_aql["qualifiers"], expected_aql["qualifiers"])
            # flag_conditions = compare_conditions(predicted_aql["conditions"], expected_aql["conditions"])

            #  Apply lowercase before comparison
            predicted_conditions = convert_conditions_to_lowercase(predicted_aql["conditions"])
            expected_conditions = convert_conditions_to_lowercase(expected_aql["conditions"])
            flag_conditions = compare_conditions(predicted_conditions, expected_conditions)

            flag_qualifiers = compare_qualifiers(predicted_aql["qualifiers"], expected_aql["qualifiers"])

            
            flag_stat_period = predicted_aql["stat_period"] == expected_aql["stat_period"]

            results.append({
                "query": query,
                "ground_truth_aql": expected_aql,
                "predicted_aql": predicted_aql,
                "flag_qualifiers": flag_qualifiers,
                "flag_conditions": flag_conditions,
                "flag_stat_period": flag_stat_period
            })
        
        time.sleep(1)  #  Prevent rate limiting

    #  Save merged results
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=4)

    print(f" Merged results saved to {OUTPUT_FILE}")

    #  Compute and print accuracy scores
    accuracy_scores = compute_accuracy(results)
    print("\n🎯 Accuracy Scores:")
    print(json.dumps(accuracy_scores, indent=4))
