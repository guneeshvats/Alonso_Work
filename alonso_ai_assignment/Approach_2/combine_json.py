import glob
import json
import os

def combine_json_files(output_folder, combined_file):
    all_data = []

    for file in glob.glob(f"{output_folder}/*.json"):
        if not os.path.getsize(file):
            print(f"Skipping empty JSON file: {file}")
            continue
        else:
            with open(file, "r") as f:
                all_data.append(json.load(f))

    with open(combined_file, "w") as outfile:
        json.dump(all_data, outfile, indent=4)
