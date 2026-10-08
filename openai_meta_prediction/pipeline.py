import os
import json
import base64
import requests
from PIL import Image, ImageDraw

# Load OpenAI API Key from config file
with open("header_prediction_config.json", "r") as f:
    api_key = json.load(f).get("api_key", "")

# Load merged JSON file
with open("FINAL_MERGED_JSON (13).json", "r") as f:
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
    print(f"✅ Saved: {output_path}")

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
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": PROMPT
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    # DEBUG: Print API response before processing
    print("RAW API RESPONSE:", response.status_code, response.text)

    # try:
    #     message = response.json()
    #     if "choices" in message:
    #         content = message["choices"][0]["message"]["content"]
    #         return json.loads(content)
    #     else:
    #         print("⚠️ WARNING: No 'choices' found in API response.")
    #         return None
    # except Exception as e:
    #     print("❌ Error parsing API response:", e)
    #     return None
    try:
        message = response.json()
        if "choices" in message:
            content = message["choices"][0]["message"]["content"]

            # DEBUGGING PRINT
            print("🚀 RAW CONTENT BEFORE CLEANING:", content)

            # Remove Markdown code block syntax
            content = content.replace("```json", "").replace("```", "").strip()

            # DEBUGGING PRINT
            print("🛠️ CLEANED CONTENT:", content)

            return json.loads(content)
        else:
            print("⚠️ WARNING: No 'choices' found in API response.")
            return None
    except Exception as e:
        print("❌ Error parsing API response:", e)
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

page_table_count = {}

# Process each table in merged JSON
for idx, table in enumerate(merged_data):
    file_name = table.get("file_name", "")
    page_no = table.get("page_no", "")
    image_path = os.path.join("images", file_name)
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        continue
    
    # Ensure table numbering starts from 1 for each page
    if page_no not in page_table_count:
        page_table_count[page_no] = 1
    else:
        page_table_count[page_no] += 1
    
    table_index = page_table_count[page_no]
    
    # Draw table on image
    output_file = f"single_tables_drawn/{file_name}_t{table_index}.png"
    draw_table(image_path, table, output_file)
    
    # Predict metadata
    predicted_metadata = predict_metadata(output_file)
    
    if not predicted_metadata:
        print(f"⚠️ WARNING: Empty prediction for {output_file}")
        predicted_metadata = {
            "entity": None,
            "statCategory": None,
            "statistic": None,
            "statPeriod": None
        }

    ground_truth = {
        "entity": table.get("entity", ""),
        "statCategory": table.get("statCategory", ""),
        "statistic": table.get("statistic", ""),
        "statPeriod": table.get("statPeriod", "")
    }
    accuracy = calculate_accuracy(ground_truth, predicted_metadata if predicted_metadata else {})
    
    result_data.append({
        "file_name": file_name,
        "page_no": page_no,
        "ground_truth": ground_truth,
        "predicted_metadata": predicted_metadata if predicted_metadata else {},
        "accuracy": accuracy
    })

# Save results to JSON
with open("results/result.json", "w") as f:
    json.dump(result_data, f, indent=4)

# Compute overall accuracy
if result_data:
    total_accuracy = sum(item["accuracy"] for item in result_data) / len(result_data)
    print(f"✅ Overall Accuracy: {total_accuracy * 100:.2f}%")
else:
    print("⚠️ No valid results were processed.")
