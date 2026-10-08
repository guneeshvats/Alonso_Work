from transformers import pipeline
import re
import json

# Load pre-trained Named Entity Recognition model
ner = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english", grouped_entities=True)

def preprocess_text(text):
    """
    Cleans and prepares text for NER parsing.
    """
    text = re.sub(r"[—~_=]+", " ", text)  # Remove noise characters
    text = re.sub(r"\s{2,}", " ", text)   # Replace multiple spaces with one
    return text.strip()

def extract_entities_with_ner(text):
    """
    Uses NER to extract relevant entities from text.
    """
    entities = ner(text)
    results = []
    for entity in entities:
        if entity["entity_group"] in ["PER", "ORG", "MISC"]:
            results.append({"entity": entity["word"], "type": entity["entity_group"]})
    return results

def parse_table_records_with_ner(raw_lines, metadata):
    """
    Parses table records using NER for structured extraction.
    """
    records = []
    for line in raw_lines:
        # Preprocess each line
        clean_line = preprocess_text(line)
        if not clean_line:
            continue

        # Extract entities
        entities = extract_entities_with_ner(clean_line)

        # Attempt to map entities to expected fields
        player_name, opponent_name, stat_value = None, None, None
        for entity in entities:
            if entity["type"] == "PER":  # Likely a player name
                player_name = entity["entity"]
            elif entity["type"] == "ORG":  # Likely an opponent
                opponent_name = entity["entity"]
            # Regex fallback for numeric stats
            if not stat_value:
                match = re.search(r"\b\d+\b", clean_line)
                if match:
                    stat_value = int(match.group())

        if player_name or opponent_name or stat_value:
            records.append({
                "playerName": player_name,
                "opponentName": opponent_name,
                "statValue": stat_value,
                "rawLine": clean_line  # Keep raw line for debugging
            })

    return {"metadata": metadata, "records": records}


# def enhanced_parsing(clean_lines, metadata):
#     """
#     Parses cleaned lines into structured records using NER and regex.
#     """
#     records = []
#     for line in clean_lines:
#         entities = ner(line)  # Apply NER
#         player, opponent, stat, extra = None, None, None, None
        
#         for entity in entities:
#             if entity["entity_group"] == "PER":
#                 player = entity["word"]
#             elif entity["entity_group"] == "ORG":
#                 opponent = entity["word"]
        
#         # Regex for numeric stats
#         stat_match = re.search(r"(\d+)\s+(yards|TD)", line)
#         if stat_match:
#             stat = int(stat_match.group(1))
#             extra = stat_match.group(2)
        
#         # Append structured record
#         records.append({
#             "playerName": player,
#             "opponentName": opponent,
#             "statValue": stat,
#             "extraStats": extra,
#             "rawLine": line
#         })
    
#     return {"metadata": metadata, "records": records}
def enhanced_parsing(clean_lines, metadata, team_list):
    """
    Parses records and distinguishes opponent names from team names.
    """
    records = []
    for line in clean_lines:
        entities = ner(line)  # Use NER to extract player names and opponents
        player_name, opponent_name, stat_value, extra_stats = None, None, None, None

        # Extract entities
        for entity in entities:
            if entity["entity_group"] == "PER":
                player_name = entity["word"]
            elif entity["entity_group"] == "ORG":
                opponent_name = entity["word"]

        # Regex for numeric stats
        stat_match = re.search(r"(\d+)\s+(yards|TD)", line)
        if stat_match:
            stat_value = int(stat_match.group(1))
            extra_stats = stat_match.group(2)

        # Check if opponent name is in the team list
        if opponent_name in team_list:
            team_name = opponent_name
            opponent_name = None  # Clear opponent name since it's a team
        else:
            team_name = None

        # Append structured record
        records.append({
            "playerName": player_name,
            "opponentName": opponent_name,
            "teamName": team_name,
            "statValue": stat_value,
            "extraStats": extra_stats,
            "rawLine": line
        })

    return {"metadata": metadata, "records": records}


# def process_parsed_tables_with_ner(input_file, output_file):
#     """
#     Processes parsed tables with advanced NER-based extraction.
#     """
#     with open(input_file, "r") as infile:
#         classified_tables = json.load(infile)

#     parsed_tables = []
#     for table in classified_tables:
#         metadata = table["metadata"]
#         raw_lines = [record["rawLine"] for record in table["records"]]
#         parsed_table = parse_table_records_with_ner(raw_lines, metadata)
#         if parsed_table["records"]:  # Include only if records exist
#             parsed_tables.append(parsed_table)

#     # Save final parsed tables to JSON
#     with open(output_file, "w") as outfile:
#         json.dump(parsed_tables, outfile, indent=4)

#     print(f"Improved parsed tables saved to {output_file}")


# Modify the final saving step to include post-processing

def post_process_records(parsed_records):
    """
    Validates and consolidates parsed records.
    """
    final_records = []
    for record in parsed_records:
        # Discard records missing key fields
        if not record["playerName"] and not record["statValue"]:
            continue
        # Ensure teamName/opponentName consistency
        if record["teamName"] and record["opponentName"]:
            record["opponentName"] = None  # Clear opponentName if teamName is valid
        final_records.append(record)

    return final_records

with open("team_list.json", "r") as team_file:
    team_list = json.load(team_file)


def process_parsed_tables_with_ner(input_file, output_file, team_list):
    """
    Processes tables with NER-based parsing and team identification.
    """
    with open(input_file, "r") as infile:
        parsed_data = json.load(infile)

    enhanced_tables = []
    for table in parsed_data:
        metadata = table["metadata"]
        processed_lines = table["processedLines"]
        parsed_table = enhanced_parsing(processed_lines, metadata, team_list)
        parsed_table["records"] = post_process_records(parsed_table["records"])
        enhanced_tables.append(parsed_table)

    with open(output_file, "w") as outfile:
        json.dump(enhanced_tables, outfile, indent=4)

    print(f"Enhanced parsed tables with team identification saved to {output_file}")


input_file = "final_parsed_tables.json"  # Current output file
output_file = "improved_parsed_tables.json"

process_parsed_tables_with_ner(input_file, output_file, team_list)
