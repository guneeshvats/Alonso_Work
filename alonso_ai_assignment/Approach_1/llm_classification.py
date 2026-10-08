import os
import json
from glob import glob
from tqdm import tqdm
from pytesseract import image_to_string
from PIL import Image
import openai  # Ensure OpenAI Python SDK is installed
from transformers import pipeline


# --- CONFIGURATION ---
openai.api_key = "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"  


# --- Step 1: Load OCR Results ---
def load_ocr_results(ocr_folder):
    """
    Load OCR results from text files.

    Parameters:
        ocr_folder (str): Path to the folder containing OCR results.

    Returns:
        list: List of dictionaries with `file_name` and `content` for each page.
    """
    ocr_files = sorted(glob(f"{ocr_folder}/*.txt"))
    ocr_data = []
    for file in ocr_files:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
        ocr_data.append({"file_name": file, "content": content})
    return ocr_data


# --- Step 2: Table Classification and Metadata Extraction ---
def classify_and_extract_metadata(page_text):
    """
    Use GPT to classify and extract metadata from page text.

    Parameters:
        page_text (str): Text extracted from a page.

    Returns:
        dict: Metadata about the table or 'Irrelevant' if not relevant.
    """
    prompt = f"""
    Below is the text extracted from a page of a sports record book. Determine if it contains a relevant table of sports statistics. 
    If relevant, extract the following metadata: 
    - Entity: Is it about a Player or Team?
    - Statistic: What statistic is being recorded? (e.g., Rushing Yards, Touchdowns)
    - StatPeriod: Is the record for a Game, Season, or Career?

    If irrelevant, respond with "Irrelevant".

    Text:
    {page_text}

    Respond in JSON format.
    """
    # response = openai.Completion.create(
    #     model="gpt-4",
    #     prompt=prompt,
    #     max_tokens=500,
    #     temperature=0.5
    # )
    response = openai.Completion.create(
        model="gpt-3.5-turbo",  
        prompt=prompt,
        max_tokens=500,
        temperature=0.5
    )    
    return response['choices'][0]['text'].strip()



def extract_table_records(page_text, metadata):
    """
    Use GPT to extract structured table records from relevant text.

    Parameters:
        page_text (str): Text extracted from the page.
        metadata (dict): Metadata extracted for the table.

    Returns:
        list: List of extracted records.
    """
    prompt = f"""
    Below is the text extracted from a sports record book page. The metadata for the table has been identified as follows:
    {json.dumps(metadata)}

    Extract the structured records from the table. Each record should include:
    - PlayerName (if applicable)
    - OpponentName (if applicable)
    - StatValue
    - Ranking (if applicable)
    - Season (if applicable)

    Respond in JSON format.

    Text:
    {page_text}
    """
    # response = openai.Completion.create(
    #     model="gpt-4",
    #     prompt=prompt,
    #     max_tokens=1000,
    #     temperature=0.5
    # )
    response = openai.Completion.create(
        model="gpt-3.5-turbo",  
        prompt=prompt,
        max_tokens=500,
        temperature=0.5
    )

    return json.loads(response['choices'][0]['text'].strip())



# --- Step 4: Combine Metadata and Records ---
def generate_output(metadata, records):
    """
    Generate the final JSON output for the table.

    Parameters:
        metadata (dict): Metadata extracted for the table.
        records (list): List of extracted records.

    Returns:
        dict: Final JSON output.
    """
    return {
        "metadata": metadata,
        "records": records
    }


# --- Step 5: Process All Pages ---
def process_all_pages(ocr_results, output_file):
    """
    Process all OCR results, classify tables, extract records, and save to JSON.

    Parameters:
        ocr_results (list): List of OCR results.
        output_file (str): Path to save the final JSON output.

    Returns:
        None
    """
    final_output = []
    for result in tqdm(ocr_results, desc="Processing Pages"):
        metadata = classify_and_extract_metadata(result['content'])
        if metadata != "Irrelevant":
            records = extract_table_records(result['content'], json.loads(metadata))
            final_output.append(generate_output(json.loads(metadata), records))

    # Save to JSON
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=4)
    print(f"Final output saved to {output_file}")


# --- MAIN FUNCTION ---
if __name__ == "__main__":
    # OCR Results Folder
    OCR_FOLDER = "ocr_output"  # Folder containing OCR results
    OUTPUT_FILE = "final_output.json"  # Path to save the final output

    # Load OCR Results
    ocr_results = load_ocr_results(OCR_FOLDER)

    # Process All Pages
    process_all_pages(ocr_results, OUTPUT_FILE)
