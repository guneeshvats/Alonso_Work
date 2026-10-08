import json

def save_to_json(metadata, records, output_file):
    data = {"metadata": metadata, "records": records}
    with open(output_file, "w") as outfile:
        json.dump(data, outfile, indent=4)
