import re
import os

def clean_text(text):
    """
    Cleans raw OCR text by removing noise and standardizing formatting.

    Parameters:
        text (str): Raw text extracted via OCR.

    Returns:
        str: Cleaned and standardized text.
    """     
    # Remove noise characters (e.g., hyphens, excessive spaces)
    text = re.sub(r"[—_=]+", " ", text)  # Replace dashes and underscores
    text = re.sub(r"\s{2,}", " ", text)   # Replace multiple spaces with one
    text = re.sub(r"^\s+|\s+$", "", text, flags=re.MULTILINE)  # Trim leading/trailing spaces
    text = text.replace("\n ", "\n")  # Remove leading spaces after line breaks
    return text

def extract_rows(cleaned_text):
    """
    Extracts table rows and structures them into a list of dictionaries.

    Parameters:
        cleaned_text (str): Cleaned OCR text.

    Returns:
        list: Structured table rows.
    """
    rows = []
    lines = cleaned_text.split("\n")
    for line in lines:
        # Regex to extract player name, opponent, and stat value
        match = re.match(r"^\d+\.\s+([A-Za-z ]+)\s+vs\.\s+([A-Za-z& ]+)\s+(\d+)", line)
        if match:
            rows.append({
                "playerName": match.group(1).strip(),
                "opponentName": match.group(2).strip(),
                "statValue": int(match.group(3).strip())
            })
    return rows



def process_and_clean_text_files(input_folder, cleaned_output_folder):
    """
    Cleans OCR text files and saves cleaned versions.

    Parameters:
        input_folder (str): Path to folder containing raw OCR text files.
        cleaned_output_folder (str): Path to folder to save cleaned text files.

    Returns:
        None
    """
    os.makedirs(cleaned_output_folder, exist_ok=True)
    files = sorted([f for f in os.listdir(input_folder) if f.endswith(".txt")])

    for file in files:
        with open(os.path.join(input_folder, file), "r") as f:
            raw_text = f.read()

        cleaned_text = clean_text(raw_text)

        with open(os.path.join(cleaned_output_folder, file), "w") as f:
            f.write(cleaned_text)

        print(f"Cleaned text saved to {cleaned_output_folder}/{file}")


input_folder = "text_outputs"  
cleaned_output_folder = "cleaned_text_outputs"

process_and_clean_text_files(input_folder, cleaned_output_folder)
