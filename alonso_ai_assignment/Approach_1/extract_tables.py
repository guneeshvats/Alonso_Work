import os
import cv2
import pytesseract
from yolov5 import YOLOv5
import json
from PIL import Image

# Step 1: Preprocessing (Image Enhancement for OCR)
def preprocess_image(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    # Apply adaptive thresholding to binarize the image
    processed_image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return processed_image

# Step 2: Table Detection using YOLOv5 (Pretrained Model for Tables)
def detect_tables(image_path, model):
    image = cv2.imread(image_path)
    results = model.predict(image)
    
    # Access bounding boxes for the first image in batch
    table_bboxes = results.pred[0]  # Access the predictions for the first image

    cropped_tables = []
    for bbox in table_bboxes:
        # Extract coordinates and convert tensor to list, then to integers
        x1, y1, x2, y2 = map(int, bbox[:4].tolist())
        cropped_tables.append(image[y1:y2, x1:x2])  # Crop table area from the image

    return cropped_tables



# Step 3: OCR on Cropped Tables
def extract_text_from_image(image):
    # Convert image to PIL format for pytesseract
    pil_image = Image.fromarray(image)
    text = pytesseract.image_to_string(pil_image, config="--psm 6")
    return text.strip()

# Step 4: Metadata and Record Extraction
def extract_metadata_and_records(ocr_text):
    # Example metadata detection
    metadata = {}
    if "rushing yards" in ocr_text.lower():
        metadata = {
            "entity": "Player",
            "statistic": "Rushing Yards",
            "statPeriod": "Game"
        }
    # Extract records (Placeholder, extend with regex or logic as needed)
    records = []
    lines = ocr_text.split("\n")
    for line in lines:
        # Example record extraction logic (adjust as per table format)
        parts = line.split()
        if len(parts) > 3:
            records.append({
                "playerName": parts[0],
                "opponentName": parts[-2],
                "statValue": parts[-1]
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

    # Load YOLO model (ensure you have the appropriate table detection weights)
    # model = YOLOv5("yolov5s-table.pt")  # Replace with your trained table detection model
    model = YOLOv5("yolov5s.pt")  # Ensure this matches the file name


    for image_file in os.listdir(input_images_folder):
        image_path = os.path.join(input_images_folder, image_file)
        print(f"Processing {image_path}...")

        # Step 1: Preprocess the image
        processed_image = preprocess_image(image_path)

        # Step 2: Detect tables
        tables = detect_tables(image_path, model)

        for i, table_image in enumerate(tables):
            # Step 3: Perform OCR on the cropped table
            ocr_text = extract_text_from_image(table_image)

            # Step 4: Extract metadata and records
            metadata, records = extract_metadata_and_records(ocr_text)

            # Step 5: Save the results to JSON
            output_file = os.path.join(output_folder, f"{os.path.splitext(image_file)[0]}_table_{i+1}.json")
            save_to_json(metadata, records, output_file)
            print(f"Saved extracted data to {output_file}")
