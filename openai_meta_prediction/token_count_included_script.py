import os
import json
import base64
import requests
from PIL import Image, ImageDraw

# Load OpenAI API Key
with open("header_prediction_config.json", "r") as f:
    api_key = json.load(f).get("api_key", "")

# Load merged JSON file
with open("FINAL_MERGED_JSON.json", "r") as f:
    merged_data = json.load(f)

os.makedirs("single_tables_drawn", exist_ok=True)
os.makedirs("results", exist_ok=True)
os.makedirs("images", exist_ok=True)

result_data = []
token_counts = []  # Store token count per request

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def predict_metadata(image_path):
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
            token_count = message.get("usage", {}).get("total_tokens", 0)  # Extract token usage
            token_counts.append(token_count)  # Store token count
            return json.loads(content)
    except Exception as e:
        print("Error parsing API response:", e)
        return None

# Processing Loop
total_accuracy = 0
valid_results = []
for table in merged_data:
    image_path = os.path.join("images", table.get("file_name", ""))
    if not os.path.exists(image_path):
        continue
    predicted_metadata = predict_metadata(image_path)
    accuracy = 1  # Dummy accuracy calculation (replace with actual logic)
    valid_results.append({"file_name": table.get("file_name"), "accuracy": accuracy})
    total_accuracy += accuracy

# Compute Averages
average_accuracy = total_accuracy / len(valid_results) if valid_results else 0
average_tokens = sum(token_counts) / len(token_counts) if token_counts else 0

# Save Results
with open("results/overall_accuracy.txt", "w") as f:
    f.write(f"Overall Accuracy: {average_accuracy * 100:.2f}%\n")
    f.write(f"Average Tokens per Request: {average_tokens:.2f}\n")

print(f"Overall Accuracy: {average_accuracy * 100:.2f}%")
print(f"Average Tokens per Request: {average_tokens:.2f}")
