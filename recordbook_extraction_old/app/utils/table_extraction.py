#############################################################################################################################
#############################################################################################################################
'''
TABLE EXTRACTION FROM COLLEGE PDF

Purpose : This script

Key Features:
    
Created by :
    Guneesh Vats
    ML Engineer, Alonzo

Dated : 
    16th Jan, 2024
    Thursday
'''
#############################################################################################################################
#############################################################################################################################

import os
import pandas as pd
import logging
import boto3
import cv2
from PIL import Image, ImageDraw
import json
from typing import List, Tuple
import re
import nltk
from nltk.translate.bleu_score import SmoothingFunction
from app.utils.progress_tracker import update_progress

logger = logging.getLogger(__name__)

###########################################################################################################################
'''                Processes the unsan.txt file to extract reference tables and their corresponding page numbers
                   Process_unsan_file() reads the text file and organizes its contents into a DataFrame    
'''
###########################################################################################################################
class UnsanProcessor:
    def __init__(self, unsan_file, include_pages = []):
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
        for i, line in enumerate(lines):
            if line.startswith('Header:'):
                match = re.search(r'PageNo\|(\d+)', line)
                if match:
                    unsan_page_no = int(match.group(1))
                    line_no = i
            elif line.strip() == '':
                if current_table and unsan_page_no is not None:
                    if not self.include_pages:
                        processed_tables.append((' '.join(current_table), unsan_page_no, line_no))

                    elif unsan_page_no in self.include_pages:
                        processed_tables.append((' '.join(current_table), unsan_page_no, line_no))

                    current_table = []
            else:
                current_table.append(line)

        if current_table and unsan_page_no is not None:
            if not self.include_pages:
                processed_tables.append((' '.join(current_table), unsan_page_no, line_no))

            elif unsan_page_no in self.include_pages:
                processed_tables.append((' '.join(current_table), unsan_page_no, line_no))

        df_unsan = pd.DataFrame(processed_tables, columns=['Table', 'PageNo', 'LineNo'])
        return df_unsan



###########################################################################################################################
'''                 Initializes a Textract client using provided AWS credentials
                    get_tables_from_image(file_path) extracts tables from an image.
                    extract_tables(response) parses Textract's response to identify tables and their bounding boxes.
'''
# #########################################################################################################################
class TextractProcessor:
    def __init__(self, config: dict):
        """
        Initializes a TextractProcessor with AWS Textract client using provided credentials.

        Args:
            config (dict): AWS configuration containing region, access key, and secret key.
        """
        self.client = boto3.client(
            'textract',
            region_name=config['region_name'],
            aws_access_key_id=config['aws_access_key_id'],
            aws_secret_access_key=config['aws_secret_access_key']
        )

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
'''                Draws bounding boxes around all detected tables on the original image
                   Saves the modified image in the specified output directory   
'''
###########################################################################################################################
def save_detected_tables(image_path: str, df_tables: pd.DataFrame, output_dir: str):
    """
    Draws bounding boxes around detected tables in an image and saves the result.

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
        color = (0, 255, 0)  # Green color for detected tables
        thickness = 2

        cv2.rectangle(image, start_point, end_point, color, thickness)

    image_name = os.path.basename(image_path)
    output_path = os.path.join(output_dir, image_name)
    cv2.imwrite(output_path, image)
    logging.info(f"Saved annotated image with tables to {output_path}.")



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



###########################################################################################################################
'''                 Extracts the page number from a given file path
                    Assumes file names are in the format ...page-XXXX.jpg
'''
# ########################################################################################################################
def get_page_number_from_filename(file_path):
    page_no_str = file_path.split('-')[-1].split('.')[0]  # Extract '0001' from '...page-0001.jpg'
    page_no = int(page_no_str)
    return page_no



###########################################################################################################################
'''                Computes the BLEU score to match extracted tables with reference tables
                   Returns a DataFrame with the mapping results    
'''
###########################################################################################################################
def get_bleu_mapping(df_image, df_unsan):
    if df_image.empty or df_unsan.empty:
        logger.warning(f"One of the DataFrames is empty! df_image: {df_image.shape}, df_unsan: {df_unsan.shape}")
    # smoothie = SmoothingFunction().method1
    mapping = []
    for _, row in df_unsan.iterrows():
        i_tab = row['Table']
        i_tab_s = list(i_tab.lower())
        unsan_page_no = row['PageNo']
        unsan_line_no = row['LineNo']

        best = [0, None, None, 0, 0, 0, 0]  # Added placeholders for bounding box data
        for _, jrow in df_image.iterrows():
            j_tab = jrow['Text']
            j_tab_s = list(j_tab.lower())

            # bleu_score = nltk.translate.bleu_score.sentence_bleu([j_tab_s], i_tab_s)
            # bleu_score = nltk.translate.bleu_score.sentence_bleu([j_tab_s], i_tab_s, smoothing_function=smoothie)
            bleu_score = nltk.translate.bleu_score.sentence_bleu([j_tab_s], i_tab_s)
            if bleu_score > best[0]:
                best = [
                    bleu_score, j_tab, jrow["TableId"],
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
            "Left": best[3],
            "Top": best[4],
            "Width": best[5],
            "Height": best[6]
        })

    mapping_df = pd.DataFrame(mapping)

    return mapping_df



###########################################################################################################################
'''                Identifies matched and unmatched tables
                   Returns separate DataFrames for matched tables, unmatched tables, and the full mapping    
'''
###########################################################################################################################
def get_matched_unmatched_tables(df_image_textract, df_unsan, dump_dir, image_name):
    mapping_textract = get_bleu_mapping(df_image_textract, df_unsan)
    mapping_textract['source'] = 'textract'

    mapping_df = mapping_textract

    # Handle case where no tables are matched
    if mapping_df.empty:
        matched_textract = pd.DataFrame()
        unmatched_textract = df_image_textract.copy()
    else:
        matched_textract = df_image_textract[
            df_image_textract['TableId'].isin(
                mapping_df[mapping_df['source'] == 'textract']['table_id']
            )
        ]
        unmatched_textract = df_image_textract[
            ~df_image_textract['TableId'].isin(
                mapping_df[mapping_df['source'] == 'textract']['table_id']
            )
        ]

    return matched_textract, unmatched_textract, mapping_df



###########################################################################################################################
'''                Draws bounding boxes around all detected tables on the original image
                   Saves the modified image in the specified output directory   
'''
###########################################################################################################################
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
        color = (0, 255, 0)  # Green color for detected tables
        thickness = 2
        cv2.rectangle(image, start_point, end_point, color, thickness)

    image_name = os.path.basename(image_path)
    output_path = os.path.join(output_dir, image_name)
    cv2.imwrite(output_path, image)



###########################################################################################################################
'''                Draws bounding boxes around matched tables on the original image
                   Saves the modified image in the specified output directory    
'''
###########################################################################################################################
def save_matched_image_with_boxes(image_path, mapping_df, output_dir):
    """
    Draws bounding boxes around matched tables on an image and saves it.

    :param image_path: Path to the original image.
    :param mapping_df: DataFrame containing 'Left', 'Top', 'Width', 'Height' columns.
    :param output_dir: Directory where the processed image should be saved.
    """
    
    if mapping_df.empty or not all(col in mapping_df.columns for col in ['Left', 'Top', 'Width', 'Height']):
        print(f"No matched tables found or missing bounding box data for {image_path}. Skipping...")
        return

    # 🔹 Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # 🔹 Load image safely
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Unable to load image {image_path}. Skipping...")
        return
    
    height, width, _ = image.shape  # Get image dimensions

    # 🔹 Draw bounding boxes
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

    # 🔹 Construct correct output filename inside function
    image_name = os.path.basename(image_path)
    output_path = os.path.join(output_dir, f"matched_{image_name}")  # Prefix with 'matched_'
    
    cv2.imwrite(output_path, image)
    print(f"Saved matched image with bounding boxes: {output_path}")



###########################################################################################################################
'''    Evaluates detection accuracy by comparing the number of matched tables with the total number of reference tables
       Saves the evaluation results to a text file   
'''
###########################################################################################################################
def evaluate_matching(output_dir, page_no, df_unsan):
    matched_file = os.path.join(output_dir, "CSV_dump/matched_tables", f"matched_page_{page_no}.csv")
    unmatched_file = os.path.join(output_dir, "CSV_dump/unmatched_tables", f"unmatched_page_{page_no}.csv")
    eval_file_path = os.path.join(output_dir, "matching_evaluation.txt")

    # Ensure required files exist before processing
    for file_path in [matched_file, unmatched_file]:
        if not os.path.exists(file_path):
            logger.warning(f"Skipping evaluation for page {page_no} due to missing file: {file_path}")
            return

    df_matched = pd.DataFrame()  # Initialize empty DataFrame
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



###########################################################################################################################
'''                Processes a single image: extracts tables, matches them, and evaluates accuracy
                   Saves output files including CSVs and images with bounding boxes   
'''
###########################################################################################################################
def process_single_image(input_image: str, unsan_file: str, config_path: str, output_dir: str, logger=None):
    if logger: 
        logger.info(f"Processing image: {input_image}")
    
    config = json.loads(open(config_path).read())
    page_no = get_page_number_from_filename(input_image)
    
    # Extracting college name from the output_dir
    college_name = os.path.basename(output_dir)

    # Extract tables using Textract
    update_progress(college_name, "Textract Processing")
    tp = TextractProcessor(config=config)
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

    # Process unsan.txt
    update_progress(college_name, "Processing Unsan File") 
    up = UnsanProcessor(unsan_file, include_pages=[page_no])
    df_unsan = up.df
    # print(f"DEBUG: Extracted {len(df_unsan)} unsan tables for page {page_no}")
    logger.debug(f"DEBUG: Extracted {len(df_unsan)} unsan tables for page {page_no}")

    # Extracting headers form unsan file 
    header = extract_header(unsan_file, page_no)

    # Get matched and unmatched tables
    update_progress(college_name, "BLEU Score Comparison")
    matched_tables, unmatched_tables, mapping_df = get_matched_unmatched_tables(df_image_textract, df_unsan, output_dir, page_no)

    matched_tables_drawn_dir = f"{output_dir}/matched_tables_drawn"
    if not matched_tables.empty:
        save_matched_image_with_boxes(input_image, matched_tables, matched_tables_drawn_dir) 
        logger.info(f"Saved matched table image in: {matched_tables_drawn_dir}")


    # Save matched/unmatched tables
    if not matched_tables.empty:
        matched_tables = matched_tables.copy()
        matched_tables["Header"] = header["Header"]
        matched_tables["TableHeader"] = header["TableHeader"]
        matched_tables.to_csv(f"{output_dir}/CSV_dump/matched_tables/matched_page_{page_no}.csv", index=False)
    else:
        logger.warning(f"No matched tables found for page {page_no}.")

    if not unmatched_tables.empty:
        unmatched_tables = unmatched_tables.copy()
        unmatched_tables["Header"] = header["Header"]
        unmatched_tables["TableHeader"] = header["TableHeader"]
        unmatched_tables.to_csv(f"{output_dir}/CSV_dump/unmatched_tables/unmatched_page_{page_no}.csv", index=False)
    else:
        logger.warning(f"No unmatched tables found for page {page_no}.")

    logger.debug(f"DEBUG: Matched Tables DataFrame:\n{matched_tables.head()}")
    logger.debug(f"DEBUG: Unmatched Tables DataFrame:\n{unmatched_tables.head()}")

    update_progress(college_name, "Saving Results")
    # Save matched/unmatched tables to JSON
    json_data = {
        "matched": matched_tables.to_dict(orient='records') if not matched_tables.empty else [],
        "unmatched": unmatched_tables.to_dict(orient='records') if not unmatched_tables.empty else [],
        "meta": {"file_name": os.path.basename(input_image), "page_no": page_no}
    }

    json_path = f"{output_dir}/matched_unmatched_json_files/page_{page_no}.json"
    with open(json_path, "w") as json_file:
        json.dump(json_data, json_file, indent=4)
    logger.debug(f"DEBUG: JSON Data Before Saving:\n{json.dumps(json_data, indent=4)}")

    # Allow evaluation to run even if files are missing
    matched_file = f"{output_dir}/CSV_dump/matched_tables/matched_page_{page_no}.csv"
    unmatched_file = f"{output_dir}/CSV_dump/unmatched_tables/unmatched_page_{page_no}.csv"

    df_matched = pd.read_csv(matched_file) if os.path.exists(matched_file) else pd.DataFrame()
    df_unmatched = pd.read_csv(unmatched_file) if os.path.exists(unmatched_file) else pd.DataFrame()

    logger.info(f"Processing page {page_no}, calling evaluate_matching even if no tables are detected.")
    evaluate_matching(output_dir=output_dir, page_no=page_no, df_unsan=df_unsan)



###########################################################################################################################
'''                Extracts headers for each table from unsan.txt files   
'''
###########################################################################################################################
def extract_header(unsan_file: str, page_no: int) -> dict:
    with open(unsan_file, 'r') as file:
        for line in file:
            if f"PageNo|{page_no}" in line:
                header = line.split(":TableHeader|")[0].replace("Header:", "").strip()
                table_header = line.split(":TableHeader|")[1].strip()
                return {"Header": header, "TableHeader": table_header}
    return {"Header": None, "TableHeader": None}



###########################################################################################################################
'''                Combines json files of each page (matched_unmatched_tables)  
'''
###########################################################################################################################

# def combine_json_files(json_dir: str, output_file: str):
#     combined_data = []
#     for file in os.listdir(json_dir):
#         if file.endswith(".json"):
#             with open(os.path.join(json_dir, file), "r") as json_file:
#                 data = json.load(json_file)

#                 # Include only "matched" tables
#                 if "matched" in data and data["matched"]:  
#                     combined_data.extend(data["matched"])  

#     # Save only the matched tables into the master JSON
#     with open(output_file, "w") as master_json:
#         json.dump(combined_data, master_json, indent=4)

    # print(f"Master JSON saved with only matched tables: {output_file}")


def combine_json_files(json_dir: str, output_file: str):
    combined_data = []

    for file in os.listdir(json_dir):
        if file.endswith(".json"):
            with open(os.path.join(json_dir, file), "r") as json_file:
                data = json.load(json_file)

                if "matched" in data and data["matched"]:
                    meta_data = data.get("meta", {})  # Extract metadata

                    # Append meta_data to each table inside "matched"
                    for table in data["matched"]:
                        table.update(meta_data)  # Merge metadata into the table
                        combined_data.append(table)

    # Save only the matched tables with metadata into the master JSON
    with open(output_file, "w") as master_json:
        json.dump(combined_data, master_json, indent=4)

##################################################   END   #################################################################
