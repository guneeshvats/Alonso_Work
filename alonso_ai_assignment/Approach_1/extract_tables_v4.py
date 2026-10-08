import os
import cv2
import pytesseract
import json
from tqdm import tqdm
from PIL import Image

# Step 1: OCR-based Full-page Text Extraction
def extract_full_page_text(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    # Enhance image quality for OCR
    processed_image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    # OCR extraction
    ocr_text = pytesseract.image_to_string(processed_image, config="--psm 6")
    return ocr_text

# Step 2: Parse Rows and Columns from Extracted Text
def parse_text_to_table(ocr_text):
    rows = ocr_text.split('\n')  # Split text into lines
    parsed_table = []
    for row in rows:
        # Split rows by whitespace while preserving aligned data
        columns = row.split()  # Adjust splitting logic if necessary for alignment
        if columns:  # Ignore empty lines
            parsed_table.append(columns)
    return parsed_table

# Step 3: Validate Table Data
def validate_table(parsed_table):
    # Check if the table contains relevant data based on keywords or patterns
    keywords = ["rushing yards", "touchdowns", "passing completions"]
    for row in parsed_table:
        for keyword in keywords:
            if keyword in ' '.join(row).lower():
                return True  # Valid table
    return False  # Invalid table

# Step 4: Extract Metadata and Records
def extract_metadata_and_records(parsed_table):
    metadata = {}
    records = []

    # Example heuristic-based metadata extraction
    if any("rushing yards" in ' '.join(row).lower() for row in parsed_table):
        metadata = {
            "entity": "Player",
            "statistic": "Rushing Yards",
            "statPeriod": "Game"
        }

    # Extract rows into structured records (adjust logic based on table format)
    for row in parsed_table:
        if len(row) > 3:  # Example condition to identify valid rows
            records.append({
                "playerName": row[0],
                "opponentName": row[-2],
                "statValue": row[-1]
            })

    return metadata, records

# Step 5: Save JSON Output
def save_to_json(metadata, records, output_file):
    data = {
        "metadata": metadata,
        "records": records
    }
    with open(output_file, "w") as outfile:
        json.dump(data, outfile, indent=4)

# Main Pipeline
if __name__ == "__main__":
    # Define paths
    input_images_folder = "output_images"  # Folder with preprocessed images
    output_folder = "output_json"
    os.makedirs(output_folder, exist_ok=True)

    image_files = os.listdir(input_images_folder)

    for image_file in tqdm(image_files, desc="Processing Images", unit="image"):
        image_path = os.path.join(input_images_folder, image_file)

        # Step 1: Extract full-page text
        ocr_text = extract_full_page_text(image_path)

        # Step 2: Parse text into table structure
        parsed_table = parse_text_to_table(ocr_text)

        # Step 3: Validate the table data
        if not validate_table(parsed_table):
            print(f"Skipping {image_file}: Table data is not valid.")
            continue

        # Step 4: Extract metadata and records
        metadata, records = extract_metadata_and_records(parsed_table)

        # Step 5: Save results to JSON
        output_file = os.path.join(output_folder, f"{os.path.splitext(image_file)[0]}.json")
        save_to_json(metadata, records, output_file)
