import json
import os
import time
from playergameSearch.views import PGSQLAdapter


# File paths
aql_input_file = "aql_input.json"  # File containing AQL queries
output_log_file = "aql_to_sql_log.json"  # Log file for storing AQL → SQL conversions

# Load AQL queries from a file
def load_aql_queries(file_path):
    """Loads AQL queries from a JSON file."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"Error loading {file_path}. Ensure it exists and is a valid JSON.")
        return []

# Convert AQL to SQL
def convert_aql_to_sql(aql_query):
    """Converts an AQL query to SQL using PGSQLAdapter."""
    adapter = PGSQLAdapter()
    sql_query, sql_params = adapter.parse_aql(aql_query)  # Get SQL & parameters
    return sql_query, sql_params

# Save AQL and SQL to a log file
def save_to_log_file(aql_query, sql_query, sql_params, file_path):
    """Appends the AQL and generated SQL to a log file."""
    log_entry = {
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "aql": aql_query,
        "generated_sql": sql_query,
        "sql_parameters": sql_params
    }

    if os.path.exists(file_path) and os.stat(file_path).st_size > 0:
        with open(file_path, "r+") as f:
            data = json.load(f)
            data.append(log_entry)
            f.seek(0)
            json.dump(data, f, indent=4)
    else:
        with open(file_path, "w") as f:
            json.dump([log_entry], f, indent=4)

# Main function
if __name__ == "__main__":
    aql_queries = load_aql_queries(aql_input_file)
    
    if not aql_queries:
        print("No valid AQL queries found.")
    else:
        for aql in aql_queries:
            print(f"Processing AQL: {json.dumps(aql, indent=2)}")
            sql_query, sql_params = convert_aql_to_sql(aql)
            save_to_log_file(aql, sql_query, sql_params, output_log_file)
            print("Saved AQL to SQL conversion in log file.\n")
