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

logs = []  # Store logs here
page_table_count = {}
valid_results = []  # Store only valid tables with ground truth

# Track accuracy sums for overall calculation
accuracy_sums = {"entity": 0, "statLabel": 0, "statPeriod": 0}
total_valid = 0  # Track number of valid tables processed

# Function to draw table bounding box
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

# Function to encode image to base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Function to send image to OpenAI and predict metadata
def predict_metadata(image_path):
    base64_image = encode_image(image_path)
    PROMPT = """
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

# Function to calculate accuracy per field
def calculate_accuracy(true_values, predicted_values):
    accuracy = {}
    for key in ["entity", "statLabel", "statPeriod"]:
        accuracy[key] = 1 if true_values.get(key) == predicted_values.get(key) else 0
    return accuracy

for table in merged_data:
    file_name = table.get("file_name", "")
    page_no = table.get("page_no", "")
    mongo_data = table.get("MongoDB_Data", {})
    if not mongo_data or "correctMappedValues" not in mongo_data:
        logs.append(f"⚠️ Skipping table in {file_name} (page {page_no}) - No ground truth available.")
        continue

    ground_truth = {
        "entity": mongo_data.get("correctMappedValues", {}).get("entity", ""),
        "statLabel": mongo_data.get("mappedValues", {}).get("statLabel", ""),
        "statPeriod": mongo_data.get("correctMappedValues", {}).get("statPeriod", "")
    }

    image_path = os.path.join("images", file_name)
    if not os.path.exists(image_path):
        logs.append(f" Image not found: {image_path}")
        continue

    predicted_metadata = predict_metadata(image_path)
    if not predicted_metadata:
        predicted_metadata = {"entity": "", "statLabel": "", "statPeriod": ""}

    accuracy = calculate_accuracy(ground_truth, predicted_metadata)
    for key in accuracy:
        accuracy_sums[key] += accuracy[key]
    total_valid += 1

    valid_results.append({
        "file_name": file_name,
        "page_no": page_no,
        "team_name": mongo_data.get("teamName", "Unknown"),
        "ground_truth": ground_truth,
        "predicted_metadata": predicted_metadata,
        "accuracy": accuracy
    })

with open("results/result.json", "w") as f:
    json.dump(valid_results, f, indent=4)

if total_valid > 0:
    overall_accuracy = {key: (accuracy_sums[key] / total_valid) * 100 for key in accuracy_sums}
else:
    overall_accuracy = {key: 0.0 for key in accuracy_sums}

with open("results/overall_accuracy.txt", "w") as f:
    for key, acc in overall_accuracy.items():
        f.write(f"{key} Accuracy: {acc:.2f}%\n")

print(" Processing complete. Results saved.")
