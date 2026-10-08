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

def encode_image(image_path):
    """
    Encodes the image to base64 format for API request.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

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

def calculate_accuracy(true_values, predicted_values):
    """
    Calculates accuracy based on how many fields are correctly predicted.
    """
    if not true_values or not predicted_values:
        return 0
    
    total_fields = len(true_values)
    correct_fields = sum(1 for key in true_values if true_values[key] == predicted_values.get(key))
    return correct_fields / total_fields if total_fields > 0 else 0

# Process each table in merged JSON
page_table_count = {}
for table in merged_data:
    file_name = table.get("file_name", "")
    page_no = table.get("page_no", "")

    #  FIXED: Get ground truth metadata correctly
    mongo_data = table.get("MongoDB_Data", {})
    ground_truth = mongo_data.get("correctMappedValues", {})

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
        print(f" Image not found: {image_path}")
        continue
    
    output_file = f"single_tables_drawn/{file_name}_t{page_table_count[page_no]}.png"
    draw_table(image_path, table, output_file)
    
    predicted_metadata = predict_metadata(output_file)
    accuracy = calculate_accuracy(ground_truth, predicted_metadata if predicted_metadata else {})
    
    result_data.append({
        "file_name": file_name,
        "page_no": page_no,
        "ground_truth": ground_truth,
        "predicted_metadata": predicted_metadata if predicted_metadata else {},
        "accuracy": accuracy
    })

# Save the results to JSON
with open("results/result.json", "w") as f:
    json.dump(result_data, f, indent=4)

# Compute and print overall accuracy
if result_data:
    total_accuracy = sum(item["accuracy"] for item in result_data) / len(result_data)
    print(f" Overall Accuracy: {total_accuracy * 100:.2f}%")
else:
    print("⚠️ No valid results were processed.")
