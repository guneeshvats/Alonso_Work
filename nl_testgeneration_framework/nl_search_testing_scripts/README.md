# Natural Language Query Testing Framework

## Overview
This framework is designed to test the accuracy of an NL Query API by comparing its output against ground truth data. It evaluates whether the generated AQL (Athlyte Query Language) responses match expected values based on qualifiers, conditions, and stat periods.

## Features
- Calls the **Natural Language Search API** to fetch AQL responses.
- Compares AQL outputs with ground truth values.
- Computes accuracy metrics based on qualifiers, conditions, and stat periods.
- Uses **Weights & Biases (WandB)** for logging and tracking predictions.
- Supports **randomized sampling** for testing.
- Saves results in structured JSON format.
- Generates log files for debugging.

## Requirements
Ensure you have the following dependencies installed before running the script:

```sh
pip install requests typer wandb rich
```

### Environment Variables
Ensure the `NL_SEARCH_API_URL` is set correctly for the API endpoint:

```python
NL_SEARCH_API_URL = "https://dev-r2.athlytesports.com/search_nl/"
```

## Usage
### Running Tests
To execute the framework, run the following command:

```sh
python script.py run <ground_truth_file.json> --num-samples <N> --randomize --outputs-dir <output_directory>
```

#### Parameters:
- `<ground_truth_file.json>`: Path to the JSON file containing ground truth data.
- `--num-samples <N>`: (Optional) Number of samples to run. If omitted, all samples will be used.
- `--randomize`: (Optional) Enables random sampling of test cases.
- `--outputs-dir <output_directory>`: (Optional) Specifies the directory for storing test results.

### Example
```sh
python script.py run ground_truth.json --num-samples 50 --randomize --outputs-dir results
```

## Output
The framework generates the following output:
1. **Logs**: Saved in `<output_directory>/log.txt`.
2. **Test Results**: JSON file containing all evaluated results.
3. **Accuracy Metrics**: Displayed in console and logged to WandB.

### Sample Output JSON
```json
[
  {
    "query": "Total passing yards by player in 2023",
    "ground_truth_aql": {...},
    "predicted_aql": {...},
    "flag_qualifiers": true,
    "flag_conditions": false,
    "flag_stat_period": true
  }
]
```

## Accuracy Computation
The framework calculates accuracy scores for:
- **Qualifiers Matching**
- **Conditions Matching**
- **Stat Period Matching**

These are logged to WandB and displayed at the end of execution.

## Logging & Tracking with WandB
This script integrates **Weights & Biases** (WandB) for tracking experiment results. Ensure you have an account at [wandb.ai](https://wandb.ai) and login using:

```sh
wandb login
```

## Contribution & Debugging
- Modify `call_nl_search()` if API response format changes.
- Adjust `compare_qualifiers()` and `compare_conditions()` for better matching logic.
- Enable logging in `log.txt` for debugging failed test cases.


