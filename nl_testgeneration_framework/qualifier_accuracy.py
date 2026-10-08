import json
import sys

def normalize(value):
    """Convert value to lowercase string for comparison."""
    return value.strip().lower() if isinstance(value, str) else value

def infer_is_home_game(conditions):
    """Infer 'isHomeGame' based on conditions."""
    if "away=1" in conditions or "home=0" in conditions:
        return "false"
    elif "home=1" in conditions or "away=0" in conditions:
        return "true"
    return None

def compare_qualifiers(gt_quals, pred_quals, conditions):
    """
    Compare ground truth and predicted qualifiers.
    Returns the count of correctly predicted qualifiers and total qualifiers.
    """
    correct = 0
    total = len(gt_quals)

    # Infer 'isHomeGame' if missing in predicted qualifiers
    if "isHomeGame" in gt_quals and "isHomeGame" not in pred_quals:
        inferred = infer_is_home_game(conditions)
        if inferred is not None:
            pred_quals["isHomeGame"] = inferred

    for key, gt_value in gt_quals.items():
        gt_value = normalize(gt_value)
        pred_value = normalize(pred_quals.get(key))

        if pred_value == gt_value:
            correct += 1

    return correct, total

def calculate_qualifier_accuracy(data):
    """Calculate the overall qualifier accuracy."""
    total_qualifiers = 0
    correct_qualifiers = 0

    for item in data:
        gt_quals = item.get("ground_truth_aql", {}).get("qualifiers", {})
        pred_quals = item.get("predicted_aql", {}).get("qualifiers", {}).copy()
        conditions = item.get("predicted_aql", {}).get("conditions", "").lower()

        # Remove 'teamName' if not present in ground truth
        if "teamName" not in gt_quals:
            pred_quals.pop("teamName", None)

        correct, total = compare_qualifiers(gt_quals, pred_quals, conditions)
        correct_qualifiers += correct
        total_qualifiers += total

    accuracy = (correct_qualifiers / total_qualifiers * 100) if total_qualifiers > 0 else 0.0
    print(f"{accuracy:.2f}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python qualifier_accuracy.py <path_to_json_file>")
        sys.exit(1)

    try:
        with open(sys.argv[1], 'r') as f:
            data = json.load(f)
        calculate_qualifier_accuracy(data)
    except Exception as e:
        print(f"Error: {e}")
        print("0.00")
        sys.exit(1)
