import re
import json

def preprocess_text(raw_lines):
    """
    Cleans and preprocesses raw OCR lines for better parsing.
    """
    processed_lines = []
    for line in raw_lines:
        # Remove OCR artifacts and normalize text
        clean_line = re.sub(r"[^\w\s.,:;()\-]", "", line)  # Remove non-alphanumeric characters
        clean_line = re.sub(r"\s{2,}", " ", clean_line)  # Replace multiple spaces with one
        clean_line = clean_line.strip()
        processed_lines.append(clean_line)
    
    # Merge multi-line records intelligently
    consolidated_lines = []
    temp_line = ""
    for line in processed_lines:
        if line.endswith(")") or line.endswith("."):
            temp_line += " " + line if temp_line else line
            consolidated_lines.append(temp_line.strip())
            temp_line = ""
        else:
            temp_line += " " + line
    
    return consolidated_lines

def advanced_preprocessing(lines):
    """
    Cleans OCR artifacts and consolidates multi-line records.
    """
    clean_lines = []
    temp_line = ""
    for line in lines:
        # Remove OCR artifacts
        line = re.sub(r"[^\w\s.,:;()\-]", "", line)  # Remove special characters
        line = re.sub(r"\s{2,}", " ", line).strip()  # Normalize spacing
        
        # Consolidate lines ending with punctuation or numeric values
        if re.search(r"[.:)]$", line) or re.search(r"\d$", line):
            temp_line += " " + line if temp_line else line
            clean_lines.append(temp_line.strip())
            temp_line = ""
        else:
            temp_line += " " + line

    return clean_lines


# Modify the preprocessing function in preprocessing script
def preprocess_raw_lines(input_file, output_file):
    """
    Preprocesses raw OCR lines by cleaning and consolidating multi-line entries.
    """
    with open(input_file, "r") as infile:
        parsed_data = json.load(infile)

    for table in parsed_data:
        raw_lines = [record["rawLine"] for record in table["records"]]
        table["processedLines"] = advanced_preprocessing(raw_lines)

    # Save the preprocessed data
    with open(output_file, "w") as outfile:
        json.dump(parsed_data, outfile, indent=4)

    print(f"Preprocessed data saved to {output_file}")

input_file = "final_parsed_tables.json"
output_file = "preprocessed_tables.json"

preprocess_raw_lines(input_file, output_file)
print(f"Preprocessed data saved to {output_file}")
