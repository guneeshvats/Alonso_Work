import re
import json
from transformers import pipeline
import torch

device = "cuda" if torch.cuda.is_available() else "cpu"
model = pipeline("text2text-generation", model="google/flan-t5-large", device=0 if device == "cuda" else -1)

def extract_from_text_llm(raw_text):
    """
    Uses an LLM to extract structured data from raw text.
    """

    instruction = (
    "Extract the following information from the text: "
    "PlayerName, OpponentName, StatValue, Ranking, and Season. "
    "If a field is not applicable, return null. "
    "Provide the result as a JSON object in strict JSON format."
    )

    prompt = f"{instruction}\n\nText: {raw_text}\n\nResult:"
    
    result = model(prompt, max_length=512, num_return_sequences=1)

    print("DEBUG: LLM Result:", result)

    extracted_data = result[0]["generated_text"]

    try:
        return json.loads(extracted_data)
    except json.JSONDecodeError:
        return {"error": "Failed to parse output", "raw_output": extracted_data}


def preprocess_raw_lines(input_file, output_file):
    """
    Preprocesses raw OCR lines by cleaning and consolidating multi-line entries.
    """
    def advanced_preprocessing(lines):
        """
        Cleans OCR artifacts and consolidates multi-line records.
        """
        clean_lines = []
        temp_line = ""
        for line in lines:
            # Remove OCR artifacts (special chars, spacing etc.)
            line = re.sub(r"[^\w\s.,:;()\-]", "", line) 
            line = re.sub(r"\s{2,}", " ", line).strip()  
            
            # Consolidate lines ending with punctuation or numeric values
            if re.search(r"[.:)]$", line) or re.search(r"\d$", line):
                temp_line += " " + line if temp_line else line
                clean_lines.append(temp_line.strip())
                temp_line = ""
            else:
                temp_line += " " + line

        return clean_lines

    with open(input_file, "r") as infile:
        parsed_data = json.load(infile)

    for table in parsed_data:
        # Extract raw lines from records
        raw_lines = [record["rawLine"] for record in table["records"]]
        # Preprocess and add back as processed lines
        table["processedLines"] = advanced_preprocessing(raw_lines)

    # Save the preprocessed data
    with open(output_file, "w") as outfile:
        json.dump(parsed_data, outfile, indent=4)

    print(f"Preprocessed data saved to {output_file}")

def process_with_llm(input_file, output_file):
    """
    Processes tables using LLM for structured data extraction.
    """
    with open(input_file, "r") as infile:
        parsed_data = json.load(infile)

    extracted_tables = []
    for table in parsed_data:
        metadata = table["metadata"]
        raw_lines = table["processedLines"]
        records = []

        for line in raw_lines:
            extracted_record = extract_from_text_llm(line)
            
            # Check if the result is valid
            if isinstance(extracted_record, dict) and "error" not in extracted_record:
                records.append(extracted_record)
            else:
                print(f"Skipping invalid output for line: {line}")
                print(f"DEBUG: Invalid Record: {extracted_record}")

        extracted_tables.append({"metadata": metadata, "records": records})

    # Save the extracted data
    with open(output_file, "w") as outfile:
        json.dump(extracted_tables, outfile, indent=4)

    print(f"Data extracted using LLM saved to {output_file}")


# File paths
input_file = "final_parsed_tables.json"  # Input from earlier processing
preprocessed_file = "preprocessed_tables.json"  # Intermediate preprocessed file
output_file = "llm_extracted_tables.json"  # Final extracted output

# Run the pipeline
preprocess_raw_lines(input_file, preprocessed_file)  # Preprocess the raw lines
process_with_llm(preprocessed_file, output_file)  # Process with LLM for extraction
