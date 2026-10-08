import re
import json

def preprocess_text(text):
    """
    Preprocesses text to standardize formatting and remove noise.
    """
    # Remove unnecessary characters and standardize spacing
    text = re.sub(r"[—~_=]+", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = text.strip()
    return text

def parse_table_records_advanced(text, metadata):
    """
    Parses rows using relaxed regex and fallback logic for inconsistent formatting.

    Parameters:
        text (str): Text content of the table.
        metadata (dict): Metadata for the table (entity, statistic, statPeriod).

    Returns:
        dict: Parsed table data with metadata and records.
    """
    records = []
    lines = text.split("\n")

    for line in lines:
        # Relaxed regex to capture player names, opponents, and values
        match = re.match(r"^\d+\.\s+([A-Za-z ]+)\s+(?:vs\.|at)\s+([A-Za-z& ]+)\s+(\d+)", line)
        if match:
            player_name = match.group(1).strip()
            opponent_name = match.group(2).strip()
            stat_value = int(match.group(3).strip())
            records.append({
                "playerName": player_name,
                "opponentName": opponent_name,
                "statValue": stat_value
            })
        else:
            # Handle cases where regex fails by looking for numeric patterns or fallback parsing
            if re.search(r"\d+", line):
                records.append({"rawLine": line.strip()})

    return {"metadata": metadata, "records": records}

def process_classified_tables(input_file, output_file):
    """
    Processes classified tables, parses records, and saves as structured JSON.

    Parameters:
        input_file (str): Path to JSON file with classified tables.
        output_file (str): Path to save the final structured JSON.

    Returns:
        None
    """
    with open(input_file, "r") as infile:
        classified_tables = json.load(infile)

    parsed_tables = []
    for table in classified_tables:
        metadata = table["metadata"]
        text = preprocess_text(table["text"])
        parsed_table = parse_table_records_advanced(text, metadata)
        if parsed_table["records"]:  # Only include tables with valid records
            parsed_tables.append(parsed_table)

    # Save parsed tables to output JSON
    with open(output_file, "w") as outfile:
        json.dump(parsed_tables, outfile, indent=4)

    print(f"Parsed tables saved to {output_file}")

# Define file paths
classified_input = "classified_tables/classified_tables.json"  # Output from Step 2
parsed_output = "final_parsed_tables.json"

# Process and parse tables
process_classified_tables(classified_input, parsed_output)
