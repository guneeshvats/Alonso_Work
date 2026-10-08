import os
import json
from glob import glob
from tqdm import tqdm
from pytesseract import image_to_string
from PIL import Image
import openai  # Ensure OpenAI Python SDK is installed
from transformers import pipeline
import torch

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")  # Use GPU if available


# Load the FLAN-T5 model
model_name = "google/flan-t5-large"  # You can replace with a smaller version if needed
model = model_name.to(device)
nlp = pipeline("text2text-generation", model=model, device=-1 if device.type == "cpu" else 0)



def classify_and_extract_metadata(page_text):
    """
    Use FLAN-T5 to classify and extract metadata from page text.

    Parameters:
        page_text (str): Text extracted from a page.

    Returns:
        str: Metadata about the table or 'Irrelevant' if not relevant.
    """
    prompt = f"""
    Extract metadata from the following text. If the text contains a relevant sports statistics table, 
    provide the following details:
    - Entity (Player or Team)
    - Statistic (e.g., Rushing Yards, Touchdowns)
    - StatPeriod (Game, Season, Career)

    If the text is irrelevant, respond with "Irrelevant".

    Text:
    {page_text}
    """
    response = nlp(prompt, max_length=512, truncation=True)
    return response[0]['generated_text']


def extract_table_records(page_text, metadata):
    """
    Use FLAN-T5 to extract structured table records from relevant text.

    Parameters:
        page_text (str): Text extracted from the page.
        metadata (str): Metadata extracted for the table.

    Returns:
        str: JSON-formatted records of the table.
    """
    prompt = f"""
    Below is the text extracted from a sports record book page. Based on the metadata:
    {metadata}
    Extract the structured records in JSON format. Each record should include:
    - PlayerName (if applicable)
    - OpponentName (if applicable)
    - StatValue
    - Ranking (if applicable)
    - Season (if applicable)

    Text:
    {page_text}
    """
    response = nlp(prompt, max_length=1024, truncation=True)
    return response[0]['generated_text']

# Example usage
page_text = "Sample text from OCR"
metadata = classify_and_extract_metadata(page_text)
if metadata != "Irrelevant":
    records = extract_table_records(page_text, metadata)
    print(records)