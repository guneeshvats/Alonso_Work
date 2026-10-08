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
    print(f" Saved table image: {output_path}")

# Function to encode image to base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Function to send image to OpenAI and predict metadata + table data
def predict_metadata(image_path):
    base64_image = encode_image(image_path)
    PROMPT = """
    You are an AI model that extracts structured metadata and table data from an image.

    The image contains a sports-related table marked with a red border. Extract the following:

    ### 1️ Metadata Extraction  
    Identify and extract the following fields:
    - "entity": Type of data in the table. Allowed values → `"Player"`, `"Team"`.  
    - "statLabel": The specific statistic represented in the table. Allowed values →  
    Blocked Kicks, Defensive Blocks, Defensive Interceptions, Defensive Passes Broken Up, Defensive QB Hurries, Defensive Rebounds, Defensive Sack Yards, Defensive Sacks (Total), Defensive Tackles (Total), Field Goals Attempted, Field Goals Blocked, Field Goals Made, Forced Fumbles, Free Throws Attempted, Free Throws Made, Fumble Recoveries, Long Field Goal, Long Receptions, Offensive Assists, Offensive First Downs, Offensive Plays, Offensive Rebounds, Offensive Yards, Passing Attempts, Passing Completions, Passing Interceptions, Passing Long, Passing Sacks, Passing Touchdowns, Passing Yards, Personal Fouls, Punt Attempts, Receiving Touchdowns, Receiving Yards, Receptions, Rushing Attempts, Rushing Touchdowns, Rushing Yards, Scoring Field Goals, Scoring PAT Kicks, Scoring Touchdowns, Steals, Tackles For Loss Yards, Tackles for Loss, Three Point Field Goals Attempted, Three Point Field Goals Made, Total Minutes, Total Points, Total Rebounds, Turnovers.  
    - "statPeriod": Time period of the statistic. Allowed values → `"Game"`, `"Season"`, `"Career"`.

    ---

    ### 2️ Table Data Extraction  
    Extract structured table data dynamically based on the `entity`:

    - Always extract: `"gameDate"`, `"season"`, `"statValue"`, `"opponentName"`.  
    - If `"entity" == "Player"` → extract `"playerName"`.  
    - If `"entity" == "Team"` → extract `"teamName"`.  

    ---

    ### 3️ Output Format  
    Return valid JSON ONLY, following this json structure (the values will depend on the input):  
    {
        "entity": "Player",
        "statLabel": "Total Points",
        "statPeriod": "Game",
        "tableData": [
            {
                "playerName": "John Doe",
                "opponentName": "Prairie View A&M",
                "gameDate": "1995-12-17",
                "season": "1995",
                "statValue": 141
            }
        ]
    }
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
        "max_tokens": 800
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    try:
        message = response.json()

        if "choices" in message:
            raw_content = message["choices"][0]["message"]["content"]
            raw_content = raw_content.replace("```json", "").replace("```", "").strip()

            return json.loads(raw_content)

    except Exception as e:
        print("⚠️ OpenAI returned malformed JSON. Skipping this table.")
        return None

# Function to calculate accuracy for metadata + table data
def calculate_table_accuracy(true_values, predicted_values):
    if not predicted_values:
        return 0
    correct_rows = 0
    total_rows = max(len(true_values), len(predicted_values))
    for true_row in true_values:
        if true_row in predicted_values:
            correct_rows += 1
    return correct_rows / total_rows if total_rows > 0 else 0

for table in merged_data:
    file_name = table.get("file_name", "")
    page_no = table.get("page_no", "")
    if page_no not in page_table_count:
        page_table_count[page_no] = 1
    else:
        page_table_count[page_no] += 1

    mongo_data = table.get("MongoDB_Data", {})
    if not mongo_data or "correctMappedValues" not in mongo_data:
        logs.append(f"⚠️ Skipping table in {file_name} (page {page_no}) - No ground truth available.")
        continue

    image_path = os.path.join("images", file_name)
    if not os.path.exists(image_path):
        logs.append(f" Image not found: {image_path}")
        continue

    output_file = f"single_tables_drawn/{file_name}_t{page_table_count[page_no]}.png"
    draw_table(image_path, table, output_file)

    predicted_metadata = predict_metadata(output_file)
    if not predicted_metadata:
        logs.append(f"⚠️ Skipping table in {file_name} (page {page_no}) - OpenAI returned invalid JSON.")
        continue

    ground_truth_table = mongo_data.get("mappedValues", {}).get("recordValues", [])
    table_accuracy = calculate_table_accuracy(ground_truth_table, predicted_metadata.get("tableData", []))

    valid_results.append({
        "file_name": file_name,
        "page_no": page_no,
        "ground_truth_metadata": mongo_data.get("correctMappedValues", {}),
        "ground_truth_table": ground_truth_table,  # Include original table data
        "predicted_metadata": predicted_metadata,
        "table_accuracy": table_accuracy
    })


with open("results/result.json", "w") as f:
    json.dump(valid_results, f, indent=4)

print(" Processing complete. Results saved.")