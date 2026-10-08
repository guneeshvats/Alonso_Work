import re
import json
from transformers import pipeline

# NER Model
ner = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english", grouped_entities=True)

# Updated enhanced_parsing
def enhanced_parsing(clean_lines, metadata, team_list):
    """
    Parses records and validates player, opponent, and team classifications,
    including ranking and season extraction.
    """
    records = []
    for line in clean_lines:
        entities = ner(line)
        player_name, opponent_name, team_name, stat_value, extra_stats, ranking, season = (
            None, None, None, None, None, None, None
        )

        # Extract entities
        for entity in entities:
            if entity["entity_group"] == "PER" and not player_name:
                player_name = entity["word"]
            elif entity["entity_group"] == "ORG":
                opponent_name = entity["word"]

        # Regex for numeric stats and secondary stats (Unit of the statValue)
        stat_match = re.search(r"(\d+)\s+(yards|TD|touchdowns)", line)
        if stat_match:
            stat_value = int(stat_match.group(1))
            extra_stats = stat_match.group(2)

        # Regex for ranking (e.g., "#1", "Rank 3")
        rank_match = re.search(r"(?:#|Rank)\s*(\d+)", line, re.IGNORECASE)
        if rank_match:
            ranking = int(rank_match.group(1))

        # Regex for season (e.g., "2020")
        season_match = re.search(r"(?:Season\s*)?(\d{4}(?:-\d{4})?)", line, re.IGNORECASE)
        if season_match:
            season = season_match.group(1)

        # Validate team names
        if opponent_name and opponent_name in team_list:
            team_name = opponent_name
            opponent_name = None

        # Ensure opponentName does not duplicate playerName
        if opponent_name == player_name:
            opponent_name = None

        # Append structured record
        if player_name or team_name or stat_value or ranking or season:
            records.append({
                "playerName": player_name,
                "opponentName": opponent_name,
                "teamName": team_name,
                "statValue": stat_value,
                "extraStats": extra_stats,
                "ranking": ranking,
                "season": season,
                "rawLine": line
            })

    return {"metadata": metadata, "records": records}


def post_process_records(parsed_records, team_list):
    """
    Filters and validates parsed records for consistency and completeness,
    including ranking and season validation.
    """
    final_records = []
    for record in parsed_records:
        # Skip records with insufficient data
        if not record["playerName"] and not record["statValue"]:
            continue

        # Validate teamName vs. opponentName
        if record["opponentName"] in team_list:
            record["teamName"] = record["opponentName"]
            record["opponentName"] = None

        # Remove redundant or noisy entries
        if record["playerName"] and record["opponentName"] == record["playerName"]:
            record["opponentName"] = None

        # Validate season (e.g., valid year format)
        if record["season"]:
            season_match = re.match(r"^\d{4}(?:-\d{4})?$", record["season"])
            if not season_match:
                record["season"] = None

        # Validate ranking (e.g., positive integers only)
        if record["ranking"] and record["ranking"] <= 0:
            record["ranking"] = None

        # Keep valid records only
        final_records.append(record)

    return final_records

def consolidate_multi_line_records(records):
    """
    Consolidates records that belong to the same player or team.
    """
    consolidated = []
    temp_record = None
    for record in records:
        if temp_record and record["playerName"] == temp_record["playerName"]:
            # Merging stats into the same record
            if record["statValue"]:
                temp_record["statValue"] += record["statValue"]
            if record["extraStats"]:
                temp_record["extraStats"] = f"{temp_record['extraStats']}, {record['extraStats']}"
        else:
            if temp_record:
                consolidated.append(temp_record)
            temp_record = record

    if temp_record:
        consolidated.append(temp_record)

    return consolidated


def validate_final_output(parsed_tables):
    """
    Validates the final JSON output for consistency and completeness.
    """
    for table in parsed_tables:
        for record in table["records"]:
            if not record["playerName"]:
                print(f"Warning: Missing playerName in record: {record}")
            if record["teamName"] and record["opponentName"]:
                print(f"Warning: teamName and opponentName conflict in record: {record}")

with open("team_list.json", "r") as team_file:
    team_list = json.load(team_file)

player_list_file = "player_list.json"
with open(player_list_file, "r") as file:
    player_list = json.load(file)

def process_parsed_tables_with_ner(input_file, output_file, team_list):
    """
    Processes tables with enhanced parsing and validation.
    """
    with open(input_file, "r") as infile:
        parsed_data = json.load(infile)

    enhanced_tables = []
    for table in parsed_data:
        metadata = table["metadata"]
        processed_lines = table["processedLines"]
        parsed_table = enhanced_parsing(processed_lines, metadata, team_list)
        parsed_table["records"] = post_process_records(parsed_table["records"], team_list)
        enhanced_tables.append(parsed_table)

    with open(output_file, "w") as outfile:
        json.dump(enhanced_tables, outfile, indent=4)

    print(f"Enhanced parsed tables saved to {output_file}")


input_file = "preprocessed_tables.json"
output_file = "enhanced_parsed_tables.json"
team_list = team_list

# Run enhanced parsing
process_parsed_tables_with_ner(input_file, output_file, team_list)
print(f"Enhanced parsed tables saved to {output_file}")
