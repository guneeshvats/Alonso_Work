import os
import cv2
import pytesseract
import json
from tqdm import tqdm
from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForCausalLM


# Step 1: OCR-based Full-page Text Extraction
def extract_full_page_text(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    # Enhance image quality for OCR
    processed_image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    # OCR extraction
    ocr_text = pytesseract.image_to_string(processed_image, config="--psm 6")
    return ocr_text

def chunk_text(text, max_length=512, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_length - overlap):
        chunks.append(" ".join(words[i:i + max_length]))
    return chunks


# Load LLM and tokenizer
# Load tokenizer and model for text generation
tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-neo-1.3B")
model = AutoModelForCausalLM.from_pretrained("EleutherAI/gpt-neo-1.3B")

# Step 2: Use LLM for Parsing and Metadata Extraction
def extract_with_llm(ocr_text):
    # Metadata prompt preparation
    metadata_prompt = (
        "Extract metadata from the following sports statistics table text. "
        "Return fields: Entity (Player/Team), Statistic (e.g., Rushing Yards), "
        "and StatPeriod (Game/Season/Career):\n\n"
        f"{ocr_text}"
    )
    # Generate metadata
    input_ids = tokenizer(metadata_prompt, return_tensors="pt", truncation=True, max_length=512).input_ids
    metadata_output = model.generate(input_ids, max_length=100)
    metadata = tokenizer.decode(metadata_output[0], skip_special_tokens=True)

    # Rows prompt preparation
    rows_prompt = (
        "Extract structured data from the following table. Return in JSON format "
        "with fields: playerName, opponentName, statValue, ranking, season:\n\n"
        f"{ocr_text}"
    )
    # Generate rows data
    input_ids = tokenizer(rows_prompt, return_tensors="pt", truncation=True, max_length=512).input_ids
    rows_output = model.generate(input_ids, max_length=300)
    records = tokenizer.decode(rows_output[0], skip_special_tokens=True)

    return metadata, records


# Step 3: Save JSON Output
def save_to_json(metadata, records, output_file):
    data = {"metadata": metadata, "records": records}
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

        # Step 2: Use LLM to extract metadata and structured data
        metadata, records = extract_with_llm(ocr_text)

        # Step 3: Save results to JSON
        output_file = os.path.join(output_folder, f"{os.path.splitext(image_file)[0]}.json")
        save_to_json(metadata, records, output_file)
