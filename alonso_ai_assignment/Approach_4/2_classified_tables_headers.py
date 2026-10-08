import os
import json

# Define keywords for classification
TABLE_HEADERS = {
    "RUSHING ATTEMPTS": {"entity": "Player", "statistic": "Rushing Attempts", "statPeriod": "Game"},
    "PASS ATTEMPTS": {"entity": "Player", "statistic": "Pass Attempts", "statPeriod": "Game"},
    "100-YARD RUSHING GAMES": {"entity": "Player", "statistic": "Rushing Yards", "statPeriod": "Game"}
}

def classify_tables(input_folder, output_folder):
    """
    Classifies tables based on their headers and assigns metadata.

    Parameters:
        input_folder (str): Path to cleaned text files.
        output_folder (str): Path to save classified metadata and tables.

    Returns:
        None
    """
    os.makedirs(output_folder, exist_ok=True)
    files = sorted([f"{input_folder}/{file}" for file in os.listdir(input_folder) if file.endswith(".txt")])
    classified_tables = []

    for file_path in files:
        with open(file_path, "r") as f:
            text = f.read()

        # Detect table type based on headers
        metadata = None
        for header, meta in TABLE_HEADERS.items():
            if header in text:
                metadata = meta
                break

        if metadata:
            # Save relevant text and metadata
            classified_tables.append({"metadata": metadata, "text": text})

    output_file = os.path.join(output_folder, "classified_tables.json")
    with open(output_file, "w") as outfile:
        json.dump(classified_tables, outfile, indent=4)

    print(f"Classified tables saved to {output_file}")

input_folder = "cleaned_text_outputs" 
output_folder = "classified_tables"   

classify_tables(input_folder, output_folder)
