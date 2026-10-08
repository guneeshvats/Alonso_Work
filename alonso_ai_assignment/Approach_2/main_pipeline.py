import os
from tqdm import tqdm
from detect_tables import detect_tables, preprocess_image
from extract_text import extract_table_text
from filter_tables import is_relevant_table
from extract_metadata import extract_metadata_and_records
from save_json import save_to_json
from combine_json import combine_json_files

# Main Pipeline
if __name__ == "__main__":
    # Define input and output paths
    input_images_folder = "output_images"  # Folder with input images
    output_folder = "output_json"
    combined_file = "final_output.json"
    os.makedirs(output_folder, exist_ok=True)

    for image_file in tqdm(os.listdir(input_images_folder), desc="Processing Images", unit="image"):
        image_path = os.path.join(input_images_folder, image_file)

        # Preprocess the image
        processed_image = preprocess_image(image_path)
        print(f"Processed image shape for {image_file}: {processed_image.shape}")

        # Step 1: Detect tables
        table_bboxes = detect_tables(processed_image)
        print(f"Detected bounding boxes for {image_file}: {table_bboxes}")  # Debug

        if not table_bboxes:
            print(f"No tables detected in {image_file}. Skipping...")
            continue

        # Step 2: Extract text from tables
        table_texts = extract_table_text(image_path, table_bboxes)
        print(f"OCR output for {image_file}: {table_texts}")  # Debug

        for i, table_text in enumerate(table_texts):
            # Step 3: Filter relevant tables
            is_relevant = is_relevant_table(table_text)
            print(f"Table relevance for {image_file}, Table {i}: {is_relevant}")  # Debug
            if not is_relevant:
                continue

            # Step 4: Extract metadata and records
            metadata, records = extract_metadata_and_records(table_text)
            print(f"Metadata for {image_file}: {metadata}")  # Debug
            print(f"Records for {image_file}: {records}")  # Debug

            if not metadata or not records:
                print(f"No valid data extracted from table {i} in {image_file}.")
                continue

            # Step 5: Save individual JSON
            output_file = os.path.join(output_folder, f"{os.path.splitext(image_file)[0]}_table_{i+1}.json")
            save_to_json(metadata, records, output_file)

    # Step 6: Combine all JSON files
    combine_json_files(output_folder, combined_file)
    print(f"Combined JSON saved to {combined_file}")


