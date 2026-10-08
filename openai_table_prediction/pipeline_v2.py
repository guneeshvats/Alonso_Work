########################################################################################################################
#                                            SPORTS TABLE EXTRACTION PIPELINE 
########################################################################################################################
'''
Purpose :
    - Extract structured metadata and table data from sports-related images.
    - Process each table by detecting its metadata and extracting relevant records.
    - Evaluate accuracy by comparing predicted results with ground truth.

Features : OpenAI API integration for metadata and table data extraction.
    - Image processing for table bounding box detection.
    - Accuracy computation for metadata and table records.
    - Logging and structured output saving


Developed By: 
    - Guneesh Vats
    - ML Engineer, Alonzo AI


Dated : 
    - 4th Feb, 2025
    - Tuesday
'''
########################################################################################################################
#                                                       IMPORTS
########################################################################################################################

import os
import os
import json
import base64
import requests
import re
from PIL import Image, ImageDraw

########################################################################################################################
''' Reads API key from configuration file.
    Required for making authenticated requests to OpenAI API 
'''
########################################################################################################################
with open("header_prediction_config.json", "r") as f:
    api_key = json.load(f).get("api_key", "")



########################################################################################################################
''' Load Merged JSON File
    Reads input data containing table images and ground truth information. 
'''
########################################################################################################################
with open("FINAL_MERGED_JSON.json", "r") as f:
    merged_data = json.load(f)



########################################################################################################################
''' Ensure Required Directories Exist
    Creates directories for storing processed images, results, and logs.
'''
########################################################################################################################
os.makedirs("single_tables_drawn", exist_ok=True)
os.makedirs("results", exist_ok=True)
os.makedirs("images", exist_ok=True)



########################################################################################################################
''' Global Variables:

    - logs: Stores processing logs.
    - page_table_count: Tracks tables per page for unique naming
    - valid_results: Stores valid extracted data.
    - metadata_accuracy_sums: Tracks accuracy of metadata fields.
    - total_metadata_valid: Counts processed valid metadata samples.
'''
########################################################################################################################
logs = []  
page_table_count = {}
valid_results = []
metadata_accuracy_sums = {"entity": 0, "statLabel": 0, "statPeriod": 0}
total_metadata_valid = 0  



########################################################################################################################
''' Function: draw_table :
    Draws a red bounding box around the detected table in the image.
    Saves the annotated image for verification
'''
########################################################################################################################
def draw_table(image_path, bbox, output_path):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    width, height = image.size
    x1 = int(bbox.get("Left", 0) * width)
    y1 = int(bbox.get("Top", 0) * height)
    x2 = int((bbox.get("Left", 0) + bbox.get("Width", 0)) * width)
    y2 = int((bbox.get("Top", 0) + bbox.get("Height", 0)) * height)
    draw.rectangle([x1, y1, x2, y2], outline="red", width=5)
    image.save(output_path)



########################################################################################################################
''' Function: encode_image :
    Converts image to base64 encoding for API request.
'''
########################################################################################################################
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')



########################################################################################################################
''' Function: extract_valid_json :
    Extracts valid JSON response from OpenAI API output using regex
'''
########################################################################################################################
def extract_valid_json(text):
    """ Extract valid JSON from API response using regex. """
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            return None
    return None



########################################################################################################################
''' Function: call_openai_api : 
    Sends API request with a prompt and an image.
    Handles response and extracts valid JSON.
'''
########################################################################################################################
def call_openai_api(prompt, image_path):
    base64_image = encode_image(image_path)
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ],
        "max_tokens": 800
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    
    try:
        message = response.json()
        if "choices" in message:
            raw_content = message["choices"][0]["message"]["content"].strip()
            return extract_valid_json(raw_content)
    except Exception as e:
        print(f"⚠️ Error calling OpenAI API: {e}")
        return None
    return None



########################################################################################################################
''' Function: predict_metadata :
    Extracts metadata information such as entity type, statistic label, and period.
'''
########################################################################################################################
def predict_metadata(image_path):
    prompt = """
        Given the above image, your task is to predict the following information for the table marked in red border in the image.

        Please provide the output in the following JSON format:
        {
             "entity": "",
             "statLabel": "",
             "statPeriod": ""
        }

        Here are all the allowed values for entity field: Player, Team
        Here are all the allowed values for the statLabel field: Blocked Kicks, Defensive Blocks, Defensive Interceptions, Defensive Passes Broken Up, Defensive QB Hurries, Defensive Rebounds, Defensive Sack Yards, Defensive Sacks (Total), Defensive Tackles (Total), Field Goals Attempted, Field Goals Blocked, Field Goals Made, Forced Fumbles, Free Throws Attempted, Free Throws Made, Fumble Recoveries, Long Field Goal, Long Receptions, Offensive Assists, Offensive First Downs, Offensive Plays, Offensive Rebounds, Offensive Yards, Passing Attempts, Passing Completions, Passing Interceptions, Passing Long, Passing Sacks, Passing Touchdowns, Passing Yards, Personal Fouls, Punt Attempts, Receiving Touchdowns, Receiving Yards, Receptions, Rushing Attempts, Rushing Touchdowns, Rushing Yards, Scoring Field Goals, Scoring PAT Kicks, Scoring Touchdowns, Steals, Tackles For Loss Yards, Tackles for Loss, Three Point Field Goals Attempted, Three Point Field Goals Made, Total Minutes, Total Points, Total Rebounds, Turnovers
        Here are all the allowed values for the statPeriod field: Game, Season, Career

        Only predict the information contained within the image. If you cannot detect any property, just fill it with null.
        Generate only JSON. It should be parseable by a program later on. DO NOT format the JSON in any markdown.
    """
    return call_openai_api(prompt, image_path)



########################################################################################################################
''' Function: predict_table_data : 
    Extracts structured table records based on predicted metadata
'''
########################################################################################################################
def predict_table_data(metadata, image_path):
    if not metadata:
        return {}

    entity = metadata.get("entity", "")
    stat_label = metadata.get("statLabel", "")
    
    prompt = f"""
        You are an AI model that extracts structured table data from an image, based on the metadata already identified.

        1️ Metadata Information  
        The table in the image corresponds to the following details:  
        - Entity Type: {{metadata['entity']}} 
        - Statistic: {{metadata['statLabel']}}  
        - Time Period: {{metadata['statPeriod']}}  


        2️ Extraction Instructions  
        Extract table rows dynamically according to the identified entity type:

        If entity == "Player"  
        Each row must contain:  
        - "playerName" → Name of the player.  
        - "opponentName" → Name of the opposing team (if available).  
        - "gameDate" → The date when the game was played (YYYY-MM-DD format, if available).  
        - "season" → Season year (YYYY format).  
        - "statValue" → The numeric value associated with "{{metadata['statLabel']}}".  

        If entity == "Team"  
        Each row must contain:  
        - "teamName" → Name of the team.  
        - "opponentName" → Name of the opposing team (if available).  
        - "gameDate" → The date when the game was played (YYYY-MM-DD format, if available).  
        - "season" → Season year (YYYY format).  
        - "statValue" → The numeric value associated with "{{metadata['statLabel']}}".  


        3️ Output Format  
        Return valid JSON ONLY, following this json structure (the output will vary based on the input and meta data predicted): 
        {{
            "entity": "{metadata['entity']}",
            "statLabel": "{metadata['statLabel']}",
            "statPeriod": "{metadata['statPeriod']}",
            "tableData": [
                {{
                    "playerName": "John Doe",
                    "opponentName": "Prairie View A&M",
                    "gameDate": "1995-12-17",
                    "season": "1995",
                    "statValue": 141
                }}
            ]
        }}
    """
    result = call_openai_api(prompt, image_path)
    return result if result else {}



########################################################################################################################
''' Function: calculate_metadata_accuracy : 
    Computes accuracy for metadata fields by comparing predictions with ground truth
'''
########################################################################################################################
def calculate_metadata_accuracy(true_values, predicted_values):
    """ Calculate accuracy for entity, statLabel, and statPeriod. """
    accuracy = {key: 1 if true_values.get(key) == predicted_values.get(key) else 0 for key in ["entity", "statLabel", "statPeriod"]}
    return accuracy




########################################################################################################################
''' Function: calculate_table_accuracy
    Computes row-wise accuracy of extracted table data
'''
########################################################################################################################
def calculate_table_accuracy(true_values, predicted_values):
    """ Calculate row-wise accuracy for table data. """
    if not predicted_values:
        return 0
    correct_rows = sum(1 for row in true_values if row in predicted_values)
    return correct_rows / max(len(true_values), len(predicted_values)) if true_values else 0



########################################################################################################################
#                                                       MAIN LOOP 
########################################################################################################################
for table in merged_data:
    file_name = table.get("file_name", "")
    page_no = table.get("page_no", "")
    if page_no not in page_table_count:
        page_table_count[page_no] = 1
    else:
        page_table_count[page_no] += 1
    
    mongo_data = table.get("MongoDB_Data", {})
    if not mongo_data:
        logs.append(f"⚠️ Skipping {file_name} (page {page_no}) - No ground truth.")
        continue
    
    image_path = os.path.join("images", file_name)
    if not os.path.exists(image_path):
        logs.append(f"⚠️ Image not found: {image_path}")
        continue
    
    output_file = f"single_tables_drawn/{file_name}_t{page_table_count[page_no]}.png"
    draw_table(image_path, table, output_file)
    
    predicted_metadata = predict_metadata(output_file)
    if not predicted_metadata:
        logs.append(f"⚠️ Failed to extract metadata for {file_name} (page {page_no}).")
        continue

    # Compute Metadata Accuracy
    ground_truth_metadata = {
        "entity": mongo_data.get("correctMappedValues", {}).get("entity", ""),
        "statLabel": mongo_data.get("mappedValues", {}).get("statLabel", ""),
        "statPeriod": mongo_data.get("correctMappedValues", {}).get("statPeriod", "")
    }
    metadata_accuracy = calculate_metadata_accuracy(ground_truth_metadata, predicted_metadata)
    
    for key in metadata_accuracy:
        metadata_accuracy_sums[key] += metadata_accuracy[key]
    total_metadata_valid += 1

    predicted_table = predict_table_data(predicted_metadata, output_file)
    ground_truth_table = mongo_data.get("mappedValues", {}).get("recordValues", [])
    table_accuracy = calculate_table_accuracy(ground_truth_table, predicted_table.get("tableData", []))
    
    valid_results.append({
        "file_name": file_name,
        "page_no": page_no,
        "predicted_metadata": predicted_metadata,
        "metadata_accuracy": metadata_accuracy,
        "predicted_table": predicted_table,
        "table_accuracy": table_accuracy,
        "ground_truth": mongo_data
    })

# Save results
with open("results/result.json", "w") as f:
    json.dump(valid_results, f, indent=4)

# Save metadata accuracy
if total_metadata_valid > 0:
    overall_metadata_accuracy = {key: (metadata_accuracy_sums[key] / total_metadata_valid) * 100 for key in metadata_accuracy_sums}
    with open("results/overall_accuracy.txt", "w") as f:
        for key, acc in overall_metadata_accuracy.items():
            f.write(f"{key} Accuracy: {acc:.2f}%\n")

print(" Processing complete. Results saved.")
