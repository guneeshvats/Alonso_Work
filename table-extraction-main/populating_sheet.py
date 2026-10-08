import os
import csv
import re

# Define the root directory containing the page folders
root_dir = "/Users/guneeshvats/Desktop/Alonso_Work/table-extraction-main/dump"
output_csv = "evaluation_sheet.csv"

# CSV headers
headers = ["Page Number", "Detected Tables", "Unsan Tables", "Matched Tables"]

# Open the CSV file for writing
with open(output_csv, mode="w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(headers)

    # Loop through each folder in the root directory
    for folder_name in sorted(os.listdir(root_dir)):
        folder_path = os.path.join(root_dir, folder_name)
        
        # Check if folder follows the pattern "page-XX"
        if os.path.isdir(folder_path) and re.match(r"page-\d{2}", folder_name):
            
            # Path to matchin_evaluation.txt
            file_path = os.path.join(folder_path, "matching_evaluation.txt")
            
            # Check if the file exists
            if os.path.exists(file_path):
                with open(file_path, "r") as file:
                    content = file.readlines()
                    
                    # Extract relevant data using regex
                    page_number = int(re.search(r"Page No:\s*(\d+)", content[0]).group(1))
                    detected_tables = int(re.search(r"Detected Tables:\s*(\d+)", content[1]).group(1))
                    unsan_tables = int(re.search(r"Unsan Tables:\s*(\d+)", content[2]).group(1))
                    matched_tables = int(re.search(r"Matched Tables:\s*(\d+)", content[3]).group(1))
                    
                    # Write data to CSV
                    writer.writerow([page_number, detected_tables, unsan_tables, matched_tables])

print(f"CSV file '{output_csv}' created successfully.")