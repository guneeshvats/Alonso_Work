import cv2
import pytesseract
import json
import pandas as pd
from pytesseract import Output
import pandas as pd
from io import StringIO
import os

# Configuration for Tesseract OCR
pytesseract.pytesseract.tesseract_cmd = r'/opt/homebrew/bin/tesseract'

# Folder paths
image_folder = "images"
output_folder = "output"

# Function to extract text using OCR
def extract_text_from_image(image_path):
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Use adaptive thresholding to enhance table regions
    processed = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )
    data = pytesseract.image_to_data(processed, output_type=Output.DICT)
    return data

# Function to extract tables using OpenCV
def extract_tables(image_path):
    image = cv2.imread(image_path, 0)
    _, binary = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY_INV)
    # Detect vertical and horizontal lines for table detection
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 20))
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 1))
    vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
    horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
    table_structure = cv2.add(vertical_lines, horizontal_lines)
    contours, _ = cv2.findContours(table_structure, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

# Function to extract metadata
def extract_metadata(text):
    metadata = {}
    if "Player" in text or "Team" in text:
        metadata["Entity"] = "Player" if "Player" in text else "Team"
    if "Game" in text:
        metadata["StatPeriod"] = "Game"
    elif "Season" in text:
        metadata["StatPeriod"] = "Season"
    elif "Career" in text:
        metadata["StatPeriod"] = "Career"
    if "Rushing" in text:
        metadata["Statistic"] = "Rushing"
    elif "Passing" in text:
        metadata["Statistic"] = "Passing"
    return metadata

# Main processing loop

def process_images(image_folder, output_folder):
    structured_data = []
    for page_num in range(1, 35):
        image_path = f"{image_folder}/page_{page_num}.png"
        image = cv2.imread(image_path, 0)  # Read as grayscale
        ocr_data = extract_text_from_image(image_path)
        text = " ".join(ocr_data['text'])
        metadata = extract_metadata(text)

        if not metadata:  # Skip irrelevant pages
            continue

        contours = extract_tables(image_path)
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            cropped_table = image[y:y + h, x:x + w]  # Crop the table region
            table_text = pytesseract.image_to_string(cropped_table, config='--psm 6')
            
            try:
                # Try parsing as CSV
                table_data = pd.read_csv(StringIO(table_text))
                for _, row in table_data.iterrows():
                    record = {
                        "PlayerName": row.get("Player", None),
                        "OpponentName": row.get("Opponent", None),
                        "StatValue": row.get("StatValue", None),
                        "Ranking": row.get("Ranking", None),
                        "Season": row.get("Season", None),
                    }
                    structured_data.append(record)
            except pd.errors.EmptyDataError:
                print(f"Failed to parse table on page {page_num}: No columns detected")
                # Fallback to manual parsing
                lines = table_text.split("\n")
                for line in lines:
                    if line.strip():  # Skip empty lines
                        fields = line.split()
                        if len(fields) >= 3:  # Adjust based on table structure
                            record = {
                                "PlayerName": fields[0],
                                "OpponentName": fields[1],
                                "StatValue": fields[2],
                            }
                            structured_data.append(record)

    # Ensure output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Save structured data to JSON
    with open(f"{output_folder}/structured_data.json", "w") as f:
        json.dump(structured_data, f, indent=4)

# Run the process
process_images(image_folder, output_folder)
