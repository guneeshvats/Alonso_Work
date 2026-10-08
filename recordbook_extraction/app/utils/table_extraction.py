#############################################################################################################################  
#                                      TABLE EXTRACTION FROM COLLEGE PDF                                                                                                                                       
#############################################################################################################################

"""
Purpose:
    - Extracts tables from college PDF documents using AWS Textract.
    - Matches extracted tables with reference tables from `unsan.txt`.
    - Stores extracted data in CSV and JSON formats.
    - Merges extracted tables with MongoDB records for validation.

Key Features:
    - Processes `unsan.txt` to extract reference table information.
    - Uses AWS Textract to extract tables from images.
    - Computes BLEU score for table matching.
    - Annotates detected tables on images.
    - Merges extracted data with MongoDB records.

Created by:
    - Guneesh Vats
    - ML Engineer, Alonzo

Dated:
    - 23rd Jan, 2024
    - Thursday
"""

#############################################################################################################################
#                                               IMPORTS                                                                                                                                               
#############################################################################################################################


import os
import pandas as pd
import logging
import boto3
import cv2
from PIL import Image, ImageDraw
import json
from bson import json_util
from typing import List, Tuple
import re
import nltk
from nltk.translate.bleu_score import SmoothingFunction
from app.utils.progress_tracker import update_progress
from app.utils.mongo_utils import get_matching_table
from pymongo import MongoClient
from app.utils.mongo_utils import get_mongo_client, clean_header
from app.utils.s3_utils import upload_to_s3 


#############################################################################################################################
#                                               LOGGING SETUP                                                                                                                                                
#############################################################################################################################


logger = logging.getLogger(__name__)


###########################################################################################################################
''' 
UnsanProcessor Class:
    - Parses `unsan.txt` to extract reference tables and their corresponding page numbers.
    - Organizes extracted tables into a DataFrame for comparison.
    - Handles cases where tables span multiple lines.
'''
###########################################################################################################################
class UnsanProcessor:
    def __init__(self, unsan_file, include_pages=[]):
        self.unsan_file = unsan_file
        self.include_pages = include_pages
        self.df = self.process_unsan_file()

    def process_unsan_file(self):
        with open(self.unsan_file, 'r') as file:
            content = file.read()

        lines = content.split('\n')

        processed_tables = []
        current_table = []
        line_no = 0
        unsan_page_no = None
        current_header = None
        current_table_header = None

        for i, line in enumerate(lines):
            if line.startswith('Header:'):
                match = re.search(r'PageNo\|(\d+)', line)
                if match:
                    unsan_page_no = int(match.group(1))
                    line_no = i
                
                # Extract Header and TableHeader
                header_split = line.split(":TableHeader|")
                current_header = header_split[0].replace("Header:", "").strip()
                current_table_header = header_split[1].strip() if len(header_split) > 1 else None

            elif line.strip() == '':
                if current_table and unsan_page_no is not None:
                    if not self.include_pages or unsan_page_no in self.include_pages:
                        processed_tables.append((
                            ' '.join(current_table),
                            unsan_page_no,
                            line_no,
                            current_header,      # Store Header
                            current_table_header # Store TableHeader
                        ))

                    current_table = []

            else:
                current_table.append(line)

        if current_table and unsan_page_no is not None:
            if not self.include_pages or unsan_page_no in self.include_pages:
                processed_tables.append((
                    ' '.join(current_table),
                    unsan_page_no,
                    line_no,
                    current_header,      # Store Header
                    current_table_header # Store TableHeader
                ))

        df_unsan = pd.DataFrame(processed_tables, columns=['Table', 'PageNo', 'LineNo', 'Header', 'TableHeader'])
        return df_unsan



###########################################################################################################################
''' 
TextractProcessor Class:
    - Initializes an AWS Textract client for table extraction.
    - Extracts table information from an image.
    - Parses Textract response to retrieve table structures and bounding boxes.
'''
###########################################################################################################################
class TextractProcessor:
    def __init__(self, textract_client):
        """
        Initializes a TextractProcessor with an existing AWS Textract client.

        Args:
            textract_client (boto3.client): Pre-authenticated Textract client.
        """
        self.client = textract_client

    def get_tables_from_image(self, image_path: str) -> pd.DataFrame:
        """
        Extracts tables from an image using AWS Textract.

        Args:
            image_path (str): Path to the image file.
        
        Returns:
            pd.DataFrame: DataFrame containing extracted table information.
        """
        logging.info(f"Processing image {image_path} with Textract.")
        with open(image_path, 'rb') as image_file:
            img_bytes = image_file.read()

        response = self.client.analyze_document(
            Document={'Bytes': img_bytes},
            FeatureTypes=['TABLES']
        )

        tables = self.extract_tables(response)
        return pd.DataFrame(tables)

    def extract_tables(self, response: dict) -> List[dict]:
        """
        Extracts table blocks from Textract response.
        """
        tables = []

        for block in response['Blocks']:
            if block['BlockType'] == 'TABLE':
                table = {
                    'TableId': block['Id'],
                    'Text': '',  # This may be empty due to parsing issues
                    'Left': block['Geometry']['BoundingBox']['Left'],
                    'Top': block['Geometry']['BoundingBox']['Top'],
                    'Width': block['Geometry']['BoundingBox']['Width'],
                    'Height': block['Geometry']['BoundingBox']['Height']
                }

                # Check if table has child relationships
                for relationship in block.get('Relationships', []):
                    if relationship['Type'] == 'CHILD':
                        for child_id in relationship['Ids']:
                            for child_block in response['Blocks']:
                                if child_block['Id'] == child_id and child_block['BlockType'] == 'CELL':
                                    cell_text = ''
                                    for cell_relationship in child_block.get('Relationships', []):
                                        if cell_relationship['Type'] == 'CHILD':
                                            for cell_child_id in cell_relationship['Ids']:
                                                for cell_child_block in response['Blocks']:
                                                    if cell_child_block['Id'] == cell_child_id and cell_child_block['BlockType'] in ['WORD', 'LINE']:
                                                        cell_text += cell_child_block.get('Text', '') + ' '

                                    table['Text'] += cell_text.strip() + ' | '

                tables.append(table)

        return tables



###########################################################################################################################
''' 
save_detected_tables():
    - Draws bounding boxes around all detected tables on an image.
    - Saves the annotated image in the specified output directory.
'''
###########################################################################################################################
def save_detected_tables(image_path: str, df_tables: pd.DataFrame, output_dir: str):
    """
    Args:
        image_path (str): Path to the image file.
        df_tables (pd.DataFrame): DataFrame containing detected tables and bounding box info.
        output_dir (str): Directory where the annotated image will be saved.
    """
    if df_tables.empty:
        logging.warning(f"No tables detected in image {image_path}. Skipping drawing.")
        return

    os.makedirs(output_dir, exist_ok=True)
    image = cv2.imread(image_path)
    height, width = image.shape[:2]

    for _, row in df_tables.iterrows():
        x = int(row['Left'] * width)
        y = int(row['Top'] * height)
        w = int(row['Width'] * width)
        h = int(row['Height'] * height)

        start_point = (x, y)
        end_point = (x + w, y + h)
        # Green color for detected tables
        color = (0, 255, 0)  
        thickness = 2

        cv2.rectangle(image, start_point, end_point, color, thickness)

    image_name = os.path.basename(image_path)
    output_path = os.path.join(output_dir, image_name)
    cv2.imwrite(output_path, image)
    logging.info(f"Saved annotated image with tables to {output_path}.")



########################################################################################################################
''' 
save_tables_to_csv():
    - Saves extracted tables to a CSV file for structured storage.
'''
########################################################################################################################
def save_tables_to_csv(df_tables: pd.DataFrame, output_path: str):
    """
    Saves the extracted tables to a CSV file.

    Args:
        df_tables (pd.DataFrame): DataFrame containing the tables.
        output_path (str): Path where the CSV file will be saved.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_tables.to_csv(output_path, index=False)
    logging.info(f"Saved extracted tables to CSV at {output_path}.")



########################################################################################################################
''' 
get_page_number_from_filename():
    - Extracts the page number from an image file path.
    - Assumes filenames follow the format: "...page-XXXX.jpg".
    - Example : Extracts '0001' from '...page-0001.jpg
'''
########################################################################################################################

def get_page_number_from_filename(file_path):
    page_no_str = file_path.split('-')[-1].split('.')[0] 
    page_no = int(page_no_str)
    return page_no



########################################################################################################################
''' 
get_bleu_mapping():
    - Computes BLEU scores to match extracted tables with reference tables.
    - Returns a DataFrame containing matching results with associated metadata.
'''
########################################################################################################################
def get_bleu_mapping(df_image, df_unsan):
    if df_image.empty or df_unsan.empty:
        logger.warning(f"One of the DataFrames is empty! df_image: {df_image.shape}, df_unsan: {df_unsan.shape}")
    
    mapping = []
    for _, row in df_unsan.iterrows():
        i_tab = row['Table']
        i_tab_s = list(i_tab.lower())
        unsan_page_no = row['PageNo']
        unsan_line_no = row['LineNo']

        best = [0, None, None, 0, 0, 0, 0]  
        for _, jrow in df_image.iterrows():
            j_tab = jrow['Text']
            j_tab_s = list(j_tab.lower())
            
            if "TableId" in jrow:  
                table_id = jrow["TableId"]
            else:
                table_id = "unmatched"

            bleu_score = nltk.translate.bleu_score.sentence_bleu([j_tab_s], i_tab_s)
            if bleu_score > best[0]:
                best = [
                    
                    bleu_score, j_tab, table_id,
                    jrow["Left"], jrow["Top"], jrow["Width"], jrow["Height"]
                ]

        mapping.append({
            "table_id": best[2] if best[2] is not None else 'unmatched',
            "image_id": best[2],
            "image_text": best[1],
            "unsan_text": i_tab,
            "bleu_score": best[0],
            "page_no": unsan_page_no,
            "line_no": unsan_line_no,
            "Header": row["Header"],            
            "TableHeader": row["TableHeader"], 
            "Left": best[3],
            "Top": best[4],
            "Width": best[5],
            "Height": best[6]
        })


    mapping_df = pd.DataFrame(mapping)

    return mapping_df



########################################################################################################################
''' 
get_matched_unmatched_tables():
    - Identifies and separates matched and unmatched tables.
    - Ensures matched tables retain their respective headers.
'''
########################################################################################################################
def get_matched_unmatched_tables(df_image_textract, df_unsan, dump_dir, image_name):
    mapping_textract = get_bleu_mapping(df_image_textract, df_unsan)
    mapping_textract['source'] = 'textract'

    mapping_df = mapping_textract

    # If df_unsan is empty, do not attempt to merge headers
    if df_unsan.empty:
        logger.warning(f"⚠️ Warning: df_unsan is empty for image {image_name}. No reference tables found in unsan.txt.")

        # All extracted tables remain unmatched since there are no reference tables
        matched_textract = pd.DataFrame()
        unmatched_textract = df_image_textract.copy()

        # Assign NULL values for unmatched tables
        unmatched_textract["Header"] = None
        unmatched_textract["TableHeader"] = None

        return matched_textract, unmatched_textract, mapping_df

    # Ensure 'TableId' column exists before attempting any operations
    if "TableId" in df_image_textract.columns:
        matched_textract = df_image_textract[
            df_image_textract['TableId'].isin(mapping_df[mapping_df['source'] == 'textract']['table_id'])
        ]
        unmatched_textract = df_image_textract[
            ~df_image_textract['TableId'].isin(mapping_df[mapping_df['source'] == 'textract']['table_id'])
        ]
    else:
        logger.warning("⚠️ Warning: 'TableId' column is missing in extracted tables!")
        matched_textract = pd.DataFrame()
        unmatched_textract = df_image_textract.copy()

    #  Merge Header & TableHeader from df_unsan into matched tables
    try:
        if not matched_textract.empty:
            matched_textract = matched_textract.merge(
                mapping_df[['table_id', 'Header', 'TableHeader']],
                left_on='TableId', right_on='table_id',
                how='left'
            ).drop(columns=['table_id'])
    except KeyError as e:
        logger.error(f"KeyError in merging headers: {str(e)}. Headers may be missing in mapping_df.")

    return matched_textract, unmatched_textract, mapping_df



########################################################################################################################
''' 
save_all_detected_tables():
    - Draws bounding boxes around all detected tables on the original image.
    - Saves the modified image with annotations.
'''
########################################################################################################################
def save_all_detected_tables(image_path, df_image_textract, output_dir="tables_drawn"):
    if df_image_textract.empty or not all(col in df_image_textract.columns for col in ['Left', 'Top', 'Width', 'Height']):
        print(f"No tables detected for {image_path}. Skipping...")
        return

    os.makedirs(output_dir, exist_ok=True)
    # Ensuring image processing doesn't fail
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"Failed to load image: {image_path}. Skipping...")
        return

    for _, row in df_image_textract.iterrows():
        x = int(row['Left'] * image.shape[1])
        y = int(row['Top'] * image.shape[0])
        w = int(row['Width'] * image.shape[1])
        h = int(row['Height'] * image.shape[0])

        start_point = (x, y)
        end_point = (x + w, y + h)
        # Green color for detected tables
        color = (0, 255, 0)  
        thickness = 2
        cv2.rectangle(image, start_point, end_point, color, thickness)

    image_name = os.path.basename(image_path)
    output_path = os.path.join(output_dir, image_name)
    cv2.imwrite(output_path, image)



########################################################################################################################
''' 
save_matched_image_with_boxes():
    - Draws bounding boxes around matched tables only.
    - Saves the modified image with annotations.
'''
########################################################################################################################
def save_matched_image_with_boxes(image_path, mapping_df, output_dir):
    """
Args - 
    :param image_path: Path to the original image.
    :param mapping_df: DataFrame containing 'Left', 'Top', 'Width', 'Height' columns.
    :param output_dir: Directory where the processed image should be saved.
    """
    
    if mapping_df.empty or not all(col in mapping_df.columns for col in ['Left', 'Top', 'Width', 'Height']):
        print(f"No matched tables found or missing bounding box data for {image_path}. Skipping...")
        return

    #  Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    #  Load image safely
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Unable to load image {image_path}. Skipping...")
        return
    
    height, width, _ = image.shape  # Get image dimensions

    #  Draw bounding boxes
    for _, row in mapping_df.iterrows():
        x = int(row['Left'] * width)   # Scale based on width
        y = int(row['Top'] * height)   # Scale based on height
        w = int(row['Width'] * width)  # Scale width
        h = int(row['Height'] * height)  # Scale height
        
        start_point = (x, y)
        end_point = (x + w, y + h)
        color = (0, 0, 255)  # Red bounding box
        thickness = 2
        cv2.rectangle(image, start_point, end_point, color, thickness)

    #  Construct correct output filename inside function
    image_name = os.path.basename(image_path)
    output_path = os.path.join(output_dir, f"matched_{image_name}")  # Prefix with 'matched_'
    
    cv2.imwrite(output_path, image)
    print(f"Saved matched image with bounding boxes: {output_path}")



########################################################################################################################
''' 
evaluate_matching():
    - Compares matched tables against reference tables to compute detection accuracy.
    - Saves evaluation results to a text file for performance analysis.
'''
########################################################################################################################
def evaluate_matching(output_dir, page_no, df_unsan):
    matched_file = os.path.join(output_dir, "CSV_dump/matched_tables", f"matched_page_{page_no}.csv")
    unmatched_file = os.path.join(output_dir, "CSV_dump/unmatched_tables", f"unmatched_page_{page_no}.csv")
    eval_file_path = os.path.join(output_dir, "matching_evaluation.txt")

    # Ensure required files exist before processing
    for file_path in [matched_file, unmatched_file]:
        if not os.path.exists(file_path):
            logger.warning(f"Skipping evaluation for page {page_no} due to missing file: {file_path}")
            return

    # Initializing empty dataframes
    df_matched = pd.DataFrame() 
    df_unmatched = pd.DataFrame()

    if os.path.exists(matched_file):
        df_matched = pd.read_csv(matched_file)
        matched_count = len(df_matched)

    if os.path.exists(unmatched_file):
        df_unmatched = pd.read_csv(unmatched_file)

    detected_count = len(df_matched) + len(df_unmatched)
    unsan_count = len(df_unsan)
    matched_count = len(df_matched)
    accuracy = (matched_count / unsan_count) * 100 if unsan_count > 0 else 0
    evaluation_output = (
        f"Page No: {page_no}\n"
        f"Detected Tables: {detected_count}\n"
        f"Unsan Tables: {unsan_count}\n"
        f"Matched Tables: {matched_count}\n"
        f"Accuracy: {accuracy:.2f}%\n\n"
    )
    with open(eval_file_path, "a") as eval_file:
        eval_file.write(evaluation_output)

    logger.info(f"Saved evaluation results to {eval_file_path} for page {page_no}.")



########################################################################################################################
''' 
process_single_image():
    - Processes a single image:
        1. Extracts tables using AWS Textract.
        2. Matches extracted tables with reference data.
        3. Saves matched and unmatched tables to CSV.
        4. Annotates images with bounding boxes.
        5. Evaluates extraction accuracy.
'''
########################################################################################################################
def process_single_image(input_image: str, unsan_file: str, textract_client, output_dir: str, logger=None):
    """
    Args:
        input_image (str): Path to the image file.
        unsan_file (str): Path to the unsan.txt file.
        textract_client (boto3.client): Pre-authenticated Textract client.
        output_dir (str): Directory where outputs are saved.
        logger: Logger instance.
    """
    if logger:
        logger.info(f"Processing image: {input_image}")

    # Extract page number from file name
    page_no = get_page_number_from_filename(input_image)
    
    # Extracting college name from the output directory
    college_name = os.path.basename(output_dir)

    # Step 1: Extract tables from the image using AWS Textract
    update_progress(college_name, "Textract Processing")
    tp = TextractProcessor(textract_client)
    df_image_textract = tp.get_tables_from_image(input_image)

    # Ensure output directories exist
    directories = [
        "CSV_dump/textract_tables",
        "CSV_dump/matched_tables",
        "CSV_dump/unmatched_tables",
        "matched_unmatched_json_files",
        "all_tables_drawn",
        "matched_tables_drawn"
    ]
    for dir_name in directories:
        os.makedirs(f"{output_dir}/{dir_name}", exist_ok=True)

    # Save CSV for Textract tables
    textract_csv_path = f"{output_dir}/CSV_dump/textract_tables/image_textract_tables_page_{page_no}.csv"
    df_image_textract.to_csv(textract_csv_path, index=False)

    # Save detected tables drawn on the images
    save_all_detected_tables(image_path=input_image, df_image_textract=df_image_textract, output_dir=f"{output_dir}/all_tables_drawn")

    # Step 2: Process unsan.txt file and extract tables
    update_progress(college_name, "Processing Unsan File")
    up = UnsanProcessor(unsan_file, include_pages=[page_no])
    df_unsan = up.df  # This now contains Table, PageNo, LineNo, Header, and TableHeader

    logger.debug(f"Extracted {len(df_unsan)} unsan tables for page {page_no}")

    # Step 3: Match extracted Textract tables with unsan tables
    update_progress(college_name, "BLEU Score Comparison")
    matched_tables, unmatched_tables, mapping_df = get_matched_unmatched_tables(df_image_textract, df_unsan, output_dir, page_no)

    # Saving Matched tables drawn on images 
    matched_tables_drawn_dir = f"{output_dir}/matched_tables_drawn"
    if not matched_tables.empty:
        save_matched_image_with_boxes(input_image, matched_tables, matched_tables_drawn_dir) 
        logger.info(f"Saved matched table image in: {matched_tables_drawn_dir}")

    # Step 4: Ensure matched tables retain their respective headers
    if not matched_tables.empty:
        matched_tables = matched_tables.copy()
        matched_tables.to_csv(f"{output_dir}/CSV_dump/matched_tables/matched_page_{page_no}.csv", index=False)
    
    else:
        logger.warning(f"No matched tables found for page {page_no}.")

    # Step 5: Ensure unmatched tables explicitly show NULL headers
    if not unmatched_tables.empty:
        unmatched_tables = unmatched_tables.copy()
        unmatched_tables["Header"] = None
        unmatched_tables["TableHeader"] = None
        unmatched_tables.to_csv(f"{output_dir}/CSV_dump/unmatched_tables/unmatched_page_{page_no}.csv", index=False)
    
    else:
        logger.warning(f"No unmatched tables found for page {page_no}.")

    # Step 6: Save JSON Output
    update_progress(college_name, "Saving Results")
    json_data = {
        "matched": matched_tables.to_dict(orient='records') if not matched_tables.empty else [],
        "unmatched": unmatched_tables.to_dict(orient='records') if not unmatched_tables.empty else [],
        "meta": {"file_name": os.path.basename(input_image), "page_no": page_no}
    }

    json_path = f"{output_dir}/matched_unmatched_json_files/page_{page_no}.json"
    with open(json_path, "w") as json_file:
        json.dump(json_data, json_file, indent=4)

    logger.debug(f"DEBUG: JSON Data Before Saving:\n{json.dumps(json_data, indent=4)}")

    # Step 7: Evaluate Matching Performance
    logger.info(f"Processing page {page_no}, calling evaluate_matching even if no tables are detected.")
    evaluate_matching(output_dir=output_dir, page_no=page_no, df_unsan=df_unsan)



########################################################################################################################
''' 
combine_json_files():
    - Combines JSON files from multiple pages into a single `master_json_file.json`.
    - Ensures matched tables retain metadata such as page number and headers.
'''
########################################################################################################################
def combine_json_files(json_dir: str, output_file: str):
    combined_data = []

    for file in os.listdir(json_dir):
        if file.endswith(".json"):
            with open(os.path.join(json_dir, file), "r") as json_file:
                data = json.load(json_file)

                if "matched" in data and data["matched"]:
                    # Extracts metadata
                    meta_data = data.get("meta", {})  

                    # Append meta_data to each table inside "matched" tables 
                    for table in data["matched"]:
                        # Merge metadata into the table
                        table.update(meta_data)
                        # Ensuring header and table-header is not lost  
                        table["Header"] = table.get("Header", None)  
                        table["TableHeader"] = table.get("TableHeader", None)
                        combined_data.append(table)

    # Save only the matched tables with metadata into the master JSON
    with open(output_file, "w") as master_json:
        json.dump(combined_data, master_json, indent=4)



########################################################################################################################
''' 
merge_with_mongo():
    - Merges the master JSON file with MongoDB records.
    - Uses case-insensitive header comparison.
    - Converts MongoDB data into a JSON-safe format.
    - Saves the final merged JSON file.
'''
########################################################################################################################
MASTER_JSON_PATH = "output-data/college_1/master_json_file.json"
MERGED_JSON_PATH = "output-data/college_1/merged_json_file.json"

def merge_with_mongo():
    print(" Starting merge_with_mongo()...")

    # Connect to MongoDB
    client = MongoClient('mongodb://mongodb:27017/')
    db = client["stage_database"]
    collection = db["StageRecords"]

    #  Print ALL headers stored in MongoDB to verify their format
    mongo_records = list(collection.find({}, {"headers": 1, "_id": 0}))  

    # Check if master file exists
    if not os.path.exists(MASTER_JSON_PATH):
        print(f" ERROR: {MASTER_JSON_PATH} not found! Skipping merge.")
        return None

    # Load master JSON file
    try:
        with open(MASTER_JSON_PATH, "r") as f:
            master_data = json.load(f)
        print(f" Loaded master_json_file.json with {len(master_data)} records")
    except Exception as e:
        print(f" ERROR: Failed to read {MASTER_JSON_PATH}: {str(e)}")
        return None

    merged_data = []
    missing_count = 0  

    for table in master_data:
        raw_header = table.get("Header", "")
        # Get cleaned list of words
        header_words = clean_header(raw_header)  

        if not header_words:
            print(f"⚠️ Skipping empty header in record: {table}")
            continue

        # Convert MongoDB headers to lowercase before comparison
        mongo_record = collection.find_one({
            "$expr": {
                "$setIsSubset": [
                    [word.lower() for word in header_words],  # Ensure lowercase search
                    {"$map": {"input": "$headers", "as": "h", "in": {"$toLower": "$$h"}}}
                ]
            }
        })


        if mongo_record:
            # Convert MongoDB record to JSON-safe format
            table["MongoDB_Data"] = json.loads(json_util.dumps(mongo_record)) 
            # print(f" Match found for header: {header_words}")
        else:
            missing_count += 1  
            print(f"⚠️ No match found for header: {header_words}")

        merged_data.append(table)

    print(f"⚠️ {missing_count} records had no MongoDB match.")  

    # Save merged JSON
    try:
        os.makedirs("output-data/college_1", exist_ok=True)  
        with open(MERGED_JSON_PATH, "w") as f:
            json.dump(merged_data, f, indent=4)
        print(f" Merged JSON saved at {MERGED_JSON_PATH}")
    except Exception as e:
        print(f" ERROR: Failed to write merged JSON: {str(e)}")
        return None  

    return MERGED_JSON_PATH
