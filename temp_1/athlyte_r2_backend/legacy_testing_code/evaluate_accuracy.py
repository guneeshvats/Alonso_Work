import json

# File paths
ground_truth_file = "ground_truth.json"
aql_log_file = "aql_query_log.json"
accuracy_report_file = "accuracy_report.txt"
merged_json_file = "merged_aql_comparison.json"

def load_json(file_path):
    """Load JSON file and return its content."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Error loading {file_path}. Ensure it exists and is a valid JSON.")
        return []

def normalize_conditions(conditions):
    """Normalize conditions by removing spaces and lowercasing for better comparison."""
    return conditions.lower().replace(" ", "")

def evaluate_accuracy():
    """Compare generated AQL queries with ground truth and compute separate accuracy for 'stat_period' and 'conditions'."""
    
    # Load both JSON files
    ground_truth_data = load_json(ground_truth_file)
    generated_aql_data = load_json(aql_log_file)

    if not ground_truth_data or not generated_aql_data:
        print("Error: Missing or empty data files.")
        return
    
    total_queries = len(ground_truth_data)
    correct_stat_period = 0
    correct_conditions = 0
    merged_data = []  # Store merged JSON data

    for ground_truth in ground_truth_data:
        query = ground_truth["query"]
        expected_stat_period = ground_truth["aql"]["stat_period"].lower()
        expected_conditions = normalize_conditions(ground_truth["aql"]["conditions"])

        # Find the corresponding query in the generated AQL log
        matched_aql = next((item for item in generated_aql_data if item["query"] == query), None)

        flag_stat_period = False
        flag_conditions = False

        if matched_aql:
            generated_stat_period = matched_aql["stat_period"].lower()
            generated_conditions = normalize_conditions(matched_aql["conditions"])

            # Check `stat_period` accuracy
            if expected_stat_period == generated_stat_period:
                correct_stat_period += 1
                flag_stat_period = True
            
            # Check `conditions` accuracy
            if expected_conditions == generated_conditions:
                correct_conditions += 1
                flag_conditions = True

        # Append to merged data
        merged_data.append({
            "query": query,
            "ground_truth": ground_truth["aql"],
            "generated_aql": matched_aql if matched_aql else {},
            "flag_stat_period": flag_stat_period,
            "flag_conditions": flag_conditions
        })

    # Compute accuracy
    stat_period_accuracy = (correct_stat_period / total_queries) * 100
    conditions_accuracy = (correct_conditions / total_queries) * 100

    # Save accuracy results to a file
    with open(accuracy_report_file, "w") as f:
        f.write(f"✅ Stat Period Accuracy: {stat_period_accuracy:.2f}% ({correct_stat_period}/{total_queries} correct)\n")
        f.write(f"✅ Conditions Accuracy: {conditions_accuracy:.2f}% ({correct_conditions}/{total_queries} correct)\n")

    # Save merged data into a JSON file
    with open(merged_json_file, "w") as f:
        json.dump(merged_data, f, indent=2)

    print(f"✅ Stat Period Accuracy: {stat_period_accuracy:.2f}% ({correct_stat_period}/{total_queries} correct)")
    print(f"✅ Conditions Accuracy: {conditions_accuracy:.2f}% ({correct_conditions}/{total_queries} correct)")
    print(f"✅ Merged JSON file created: {merged_json_file}")

if __name__ == "__main__":
    evaluate_accuracy()
