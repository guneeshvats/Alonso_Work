#########################################################################################################################
#                                         TABLE METADATA EXTRACTION PIPELINE             
#########################################################################################################################
'''
Title : Table Metadata Extraction Pipeline
Purpose : 
    This script processes images containing tables, extracts table metadata using OpenAI's GPT-4 model, 
    and evaluates the accuracy of the extracted data against ground truth values from a merged JSON file.

Features :
    - Loads table metadata from a JSON file (`FINAL_MERGED_JSON.json`).
    - Draws bounding boxes around detected tables in images.
    - Sends table images to OpenAI API for metadata prediction.
    - Compares predicted metadata with ground truth from MongoDB data.
    - Computes and stores accuracy for each table.
    - Saves results in `result.json` and overall accuracy in `overall_accuracy.txt`.

Developed By :
    Guneesh Vats
    ML Engineer, Alonzo

Dated : 
    31st Jan, 2025
    Friday 
'''
#########################################################################################################################
#                                                    IMPORTS
#########################################################################################################################

import os
import json
import base64
import requests
from PIL import Image, ImageDraw

# Load OpenAI API Key from config file
with open("header_prediction_config.json", "r") as f:
    api_key = json.load(f).get("api_key", "")

# Load merged JSON file
with open("FINAL_MERGED_JSON.json", "r") as f:
    merged_data = json.load(f)

# Ensure directories exist
os.makedirs("single_tables_drawn", exist_ok=True)
os.makedirs("results", exist_ok=True)
os.makedirs("images", exist_ok=True)

result_data = []

#########################################################################################################################
'''
Function : draw_table
Purpose  : 
    Draws a red boundary around the detected table in an image using the provided bounding box coordinates.
Arguments:
    - image_path : str : Path to the original image file.
    - bbox       : dict : Dictionary containing the bounding box coordinates (Left, Top, Width, Height).
    - output_path: str : Path where the processed image with the bounding box should be saved.
Returns  : None
'''
#########################################################################################################################
def draw_table(image_path, bbox, output_path):
    """
    Draws a red boundary around a table on the image and saves it.
    """
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    
    width, height = image.size
    x1 = int(bbox.get("Left", 0) * width)
    y1 = int(bbox.get("Top", 0) * height)
    x2 = int((bbox.get("Left", 0) + bbox.get("Width", 0)) * width)
    y2 = int((bbox.get("Top", 0) + bbox.get("Height", 0)) * height)
    
    draw.rectangle([x1, y1, x2, y2], outline="red", width=5)
    image.save(output_path)
    print(f" Saved: {output_path}")



#########################################################################################################################
'''
Function : encode_image
Purpose  : 
    Converts an image into a base64-encoded string for API request.
Arguments:
    - image_path : str : Path to the image file.
Returns  : str : Base64-encoded image content.
'''
#########################################################################################################################

def encode_image(image_path):
    """
    Encodes the image to base64 format for API request.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')



#########################################################################################################################
'''
Function : predict_metadata
Purpose  : 
    Sends a base64-encoded table image to OpenAI GPT-4 model and retrieves the predicted metadata.
Arguments:
    - image_path : str : Path to the table image file.
Returns  : dict | None : Extracted metadata in JSON format or None if an error occurs.
'''
#########################################################################################################################
def predict_metadata(image_path):
    """
    Sends an image to OpenAI API and predicts metadata.
    """
    base64_image = encode_image(image_path)
    
    PROMPT = """
    Given the above image, your task is to predict the following information for the table marked in red border in the image. 

    Note that the image has information about sports records. It has a main header, followed by a series of subheaders. The image is also split into columns. So, please take that into consideration. Predict the following data accurately.

    Please give output in the following JSON format:

    {
         "entity" : "",
         "statCategory" : "",
         "statistic" : "",
         "statPeriod" : ""
    }

    Here are all the allowed values for entity field : Player, Team

    Here are all the allowed values for the statCategory field : Defense , Field Goals , Kickoff Returns , Offense , PATs , Passing , Punt Returns , Punt , Receiving , Rushing , Scoring , Special Teams

    Here are all the allowed values for the statistic field : Attempted , Attempts , Completed , First Downs , Fumble , Interceptions , Long , Made , Plays , Points , Receptions , Sacks(Total) , Tackles for Loss , Tackles(Total) , Touchdowns , Yards

    Here are all the allowed values for the statPeriod field: Game, Season, Career

    Only predict the information contained within the image. If you cannot detect any property, just fill it with null. Remember that you can fill in a field only with the list of values allowed for the field. Pay attention to the sequence in which the table occurs, as that determines information necessary for this task. 

    Important ! : For this purpose, only consider the headers which occur before the table and not after it.

    Generate only JSON. It should be parseable by a program later on. DO NOT format the JSON in any markdown.
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "user", "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ],
        "max_tokens": 300
    }
    
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    try:
        message = response.json()
        if "choices" in message:
            content = message["choices"][0]["message"]["content"].replace("```json", "").replace("```", "").strip()
            return json.loads(content)
    except Exception as e:
        print(" Error parsing API response:", e)
        return None



#########################################################################################################################
'''
Function : calculate_accuracy
Purpose  : 
    Computes the accuracy of the predicted metadata by comparing it with ground truth values.
Arguments:
    - true_values     : dict : Dictionary containing the ground truth metadata.
    - predicted_values: dict : Dictionary containing the predicted metadata.
Returns  : float : Accuracy as a fraction (0 to 1).
'''
#########################################################################################################################
def calculate_accuracy(true_values, predicted_values):
    """
    Calculates accuracy based on how many fields are correctly predicted.
    """
    if not true_values or not predicted_values:
        return 0
    
    total_fields = len(true_values)
    correct_fields = sum(1 for key in true_values if true_values[key] == predicted_values.get(key))
    return correct_fields / total_fields if total_fields > 0 else 0



#########################################################################################################################
'''
Main Processing Loop
Purpose  : 
    - Iterates through each table in `FINAL_MERGED_JSON.json`.
    - Loads ground truth metadata from MongoDB data.
    - Extracts `teamName` and table properties.
    - Draws table bounding box on the corresponding image.
    - Sends image to OpenAI API for metadata prediction.
    - Compares predictions with ground truth and calculates accuracy.
    - Saves results in `results/result.json`.
    - Computes and stores overall accuracy in `results/overall_accuracy.txt`.
'''
#########################################################################################################################
logs = []  # Store logs here
# Process each table in merged JSON
page_table_count = {}
valid_results = []  # Store only valid tables with ground truth

for table in merged_data:
    file_name = table.get("file_name", "")
    page_no = table.get("page_no", "")

    # Retrieve MongoDB Data
    mongo_data = table.get("MongoDB_Data", {})
    
    # Skip tables that have NO ground truth
    if not mongo_data or "correctMappedValues" not in mongo_data:
        log_msg = f"⚠️ Skipping table in {file_name} (page {page_no}) - No ground truth available."
        print(log_msg)
        logs.append(log_msg)
        continue

    ground_truth = mongo_data.get("correctMappedValues", {})
    team_name = mongo_data.get("teamName", "Unknown")  # Default to "Unknown" if not found

    # Ensure the ground truth fields exist
    ground_truth = {
        "entity": ground_truth.get("entity", ""),
        "statCategory": ground_truth.get("statCategory", ""),
        "statistic": ground_truth.get("statistic", ""),
        "statPeriod": ground_truth.get("statPeriod", "")
    }
    
    if page_no not in page_table_count:
        page_table_count[page_no] = 1
    else:
        page_table_count[page_no] += 1
    
    image_path = os.path.join("images", file_name)
    if not os.path.exists(image_path):
        log_msg = f" Image not found: {image_path}"
        print(log_msg)
        logs.append(log_msg)
        continue
    
    output_file = f"single_tables_drawn/{file_name}_t{page_table_count[page_no]}.png"
    draw_table(image_path, table, output_file)
    logs.append(f" Processed table image: {output_file}")  # Log success
    
    predicted_metadata = predict_metadata(output_file)
    accuracy = calculate_accuracy(ground_truth, predicted_metadata if predicted_metadata else {})
    
    valid_results.append({
        "file_name": file_name,
        "page_no": page_no,
        "team_name": team_name,
        "ground_truth": ground_truth,
        "predicted_metadata": predicted_metadata if predicted_metadata else {},
        "accuracy": accuracy
    })
    logs.append(f" Accuracy for {file_name} (Page {page_no}): {accuracy:.2%}")

# Save the valid results to JSON
with open("results/result.json", "w") as f:
    json.dump(valid_results, f, indent=4)

# Compute overall accuracy ONLY for valid results
if valid_results:
    total_accuracy = sum(item["accuracy"] for item in valid_results) / len(valid_results)
    print(f" Overall Accuracy: {total_accuracy * 100:.2f}%")
    
    # Save overall accuracy to a text file
    with open("results/overall_accuracy.txt", "w") as f:
        f.write(f"Overall Accuracy: {total_accuracy * 100:.2f}%\n")
else:
    print("⚠️ No valid results were processed (all missing ground truth).")
    with open("results/overall_accuracy.txt", "w") as f:
        f.write("Overall Accuracy: 0.00%\n")

        # Save logs to a file
    with open("results/logs.txt", "w") as log_file:
        log_file.write("\n".join(logs) + "\n")

    print(" Logs saved to results/logs.txt")

