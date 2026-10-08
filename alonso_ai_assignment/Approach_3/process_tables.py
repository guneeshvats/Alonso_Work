import os
import pytesseract
import json

def extract_text_from_image(image_path):
    # Configure tesseract for better accuracy
    config = '--oem 3 --psm 6'
    return pytesseract.image_to_string(image_path, config=config)

def filter_relevant_tables(text):
    # Keywords to detect relevant tables
    keywords = ["Player", "Opponent", "Yards", "Touchdowns", "Passing"]
    return any(keyword in text for keyword in keywords)

def extract_attributes(text):
    # Use regex or heuristics to extract metadata and records
    metadata = {
        "entity": "Player",
        "statPeriod": "Game",
        "statistic": "Pass Attempts"
    }
    records = [
        {"playerName": "Tyler Wilson", "opponentName": "Texas A&M", "statValue": 59, "ranking": 1, "season": 2012}
    ]
    return metadata, records

def save_to_json(data, output_file):
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    cropped_table_dir = 'results/results/crops/'  # YOLO crop directory
    final_data = []

    for table_image in os.listdir(cropped_table_dir):
        image_path = os.path.join(cropped_table_dir, table_image)
        table_text = extract_text_from_image(image_path)

        if filter_relevant_tables(table_text):
            metadata, records = extract_attributes(table_text)
            final_data.append({"metadata": metadata, "records": records})

    save_to_json(final_data, "output.json")
