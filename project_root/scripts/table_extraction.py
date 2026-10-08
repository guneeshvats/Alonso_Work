#############################################################################################################################
#############################################################################################################################
'''
Purpose : This script establishes a connection with AWS S3 to process PDF documents and extract tabular data using Amazon Textract. 
    It converts PDF pages to images, extracts tables from these images, matches them with reference tables from text files, 
    and evaluates the results for accuracy. The processed data is saved locally and uploaded to S3. 

Key Features:
    - Converts PDF pages to high-resolution images.
    - Uses Amazon Textract to extract tables from images.
    - Matches extracted tables with reference tables using BLEU score for similarity evaluation.
    - Annotates images with bounding boxes for matched tables.
    - Generates reports, evaluation files, and uploads results to S3.

Created by :
    Guneesh Vats
    ML Engineer, Alonzo


Dated : 
    9th Jan, 2024
    Thursday
'''
#############################################################################################################################
#############################################################################################################################

import boto3
import pandas as pd
import os
import re
import nltk
import sys
import json
from PIL import Image, ImageDraw
import typer
import cv2
import shutil
import tqdm
from pdf2image import convert_from_path
import time 
import logging
from logging.handlers import RotatingFileHandler

###########################################################################################################################
'''                 Saving the logs after running this file in logs.txt
'''
# ########################################################################################################################
log_file = "logs.txt"
logging.basicConfig(
    level=logging.INFO,  # Set log level to INFO
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),  # Log to file
        logging.StreamHandler()         # Log to terminal
    ]
)

app = typer.Typer()
s3_client = boto3.client('s3')

###########################################################################################################################
'''                 Converting pdf pages into images and saving in a folder
'''
# ########################################################################################################################
def convert_pdf_to_images(pdf_path, images_dir):
    """ Converts PDF to images and saves them in the specified directory as PNG. """
    os.makedirs(images_dir, exist_ok=True)
    pages = convert_from_path(pdf_path, dpi=300)  # Use high DPI for better image quality
    for i, page in enumerate(pages):
        image_path = os.path.join(images_dir, f'page-{i + 1:04d}.png')  # Save as PNG
        page.save(image_path, 'PNG')  # Use PNG format
        time.sleep(0.1) # small delay to ensure porper write
        logging.info(f"Saved page {i + 1} as {image_path}")
        print(f"Saved page {i + 1} as {image_path}")
        


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
'''                 Initializes a Textract client using provided AWS credentials
                    get_tables_from_image(file_path) extracts tables from an image.
                    extract_tables(response) parses Textract's response to identify tables and their bounding boxes.
'''
# #########################################################################################################################
class TextractProcessor:
    def __init__(self, config):
        self.client = boto3.client('textract', region_name=config['region_name'],
                                   aws_access_key_id=config['aws_access_key_id'],
                                   aws_secret_access_key=config['aws_secret_access_key'])

    def get_tables_from_image(self, file_path):
        with open(file_path, 'rb') as image:
            img = bytearray(image.read())
            response = self.client.analyze_document(
                Document={'Bytes': img},
                FeatureTypes=['LAYOUT', 'TABLES']
            )
            tables = self.extract_tables(response)

            page_no = get_page_number_from_filename(file_path)

            df = pd.DataFrame(tables)
            df['PageNo'] = page_no

            return df

    def extract_tables(self, response):
        tables = []

        for block in response['Blocks']:
            if block['BlockType'] == 'TABLE':
                table = {
                    'TableId': block['Id'],
                    'Text': '',
                    'Left': block['Geometry']['BoundingBox']['Left'],
                    'Top': block['Geometry']['BoundingBox']['Top'],
                    'Width': block['Geometry']['BoundingBox']['Width'],
                    'Height': block['Geometry']['BoundingBox']['Height']
                }
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
                                                    if cell_child_block['Id'] == cell_child_id and cell_child_block[
                                                        'BlockType'] == 'WORD':
                                                        cell_text += cell_child_block['Text'] + ' '
                                    table['Text'] += cell_text.strip() + ' | '
                tables.append(table)
        return tables



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
'''                Computes the BLEU score to match extracted tables with reference tables
                   Returns a DataFrame with the mapping results    
'''
###########################################################################################################################
def get_bleu_mapping(df_image, df_unsan):
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
'''                Draws bounding boxes around matched tables on the original image
                   Saves the modified image in the specified output directory    
'''
###########################################################################################################################
def save_matched_image_with_boxes(image_path, mapping_df, output_dir="matched_tables_drawn"):
    if mapping_df.empty or not all(col in mapping_df.columns for col in ['Left', 'Top', 'Width', 'Height']):
        print(f"No matched tables found or missing bounding box data for {image_path}. Skipping...")
        return

    os.makedirs(output_dir, exist_ok=True)
    image = cv2.imread(image_path)

    for _, row in mapping_df.iterrows():
        x = int(row['Left'] * image.shape[1])
        y = int(row['Top'] * image.shape[0])
        w = int(row['Width'] * image.shape[1])
        h = int(row['Height'] * image.shape[0])
        
        start_point = (x, y)
        end_point = (x + w, y + h)
        color = (0, 0, 255)
        thickness = 2
        cv2.rectangle(image, start_point, end_point, color, thickness)

    image_name = os.path.basename(image_path)
    output_path = os.path.join(output_dir, image_name)
    cv2.imwrite(output_path, image)



###########################################################################################################################
'''    Evaluates detection accuracy by comparing the number of matched tables with the total number of reference tables
       Saves the evaluation results to a text file   
'''
###########################################################################################################################
def evaluate_matching(output_dir, page_no):
    matched_file = os.path.join(output_dir, "matched.csv")
    unmatched_file = os.path.join(output_dir, "unmatched.csv")
    unsan_file = os.path.join(output_dir, "unsan_tables.csv")
    eval_file_path = os.path.join(output_dir, "matching_evaluation.txt")

    df_matched = pd.read_csv(matched_file)
    df_unmatched = pd.read_csv(unmatched_file)
    df_unsan = pd.read_csv(unsan_file)

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
    image = cv2.imread(image_path)

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
'''                Processes a single image: extracts tables, matches them, and evaluates accuracy
                   Saves output files including CSVs and images with bounding boxes   
'''
###########################################################################################################################
def process_single_image(input_image: str, unsan_file: str, config_path: str, output_dir: str):
    config = json.loads(open(config_path).read())
    tp = TextractProcessor(config=config)

    page_no = get_page_number_from_filename(input_image)
    up = UnsanProcessor(unsan_file, include_pages=[page_no])

    # Ensure necessary subdirectories exist
    textract_dir = os.path.join(output_dir, "dump", "textract_tables")
    matched_dir = os.path.join(output_dir, "dump", "matched_tables")
    unmatched_dir = os.path.join(output_dir, "dump", "unmatched_tables")
    json_dir = os.path.join(output_dir, "json_files")
    drawn_dir = os.path.join(output_dir, "matched_tables_drawn")
    tables_drawn_dir = os.path.join(output_dir, "tables_drawn")
    
    os.makedirs(textract_dir, exist_ok=True)
    os.makedirs(matched_dir, exist_ok=True)
    os.makedirs(unmatched_dir, exist_ok=True)
    os.makedirs(json_dir, exist_ok=True)
    os.makedirs(drawn_dir, exist_ok=True)
    os.makedirs(tables_drawn_dir, exist_ok=True)

    # Extract tables using Textract and save intermediate results
    df_image_textract = tp.get_tables_from_image(input_image)
    df_image_textract.to_csv(os.path.join(textract_dir, f"image_textract_tables_page_{page_no}.csv"))

    # Save detected tables drawn on the images
    save_all_detected_tables(input_image, df_image_textract, output_dir=os.path.join(output_dir, "tables_drawn"))

    # Process unsanctioned tables and save
    df_unsan = up.df

    image_name = os.path.splitext(os.path.basename(input_image))[0]
    matched_tables, unmatched_tables, mapping_df = get_matched_unmatched_tables(
        df_image_textract, df_unsan, textract_dir, image_name
    )

    unmatched_tables.to_csv(os.path.join(unmatched_dir, f"unmatched_page_{page_no}.csv"))
    matched_tables.to_csv(os.path.join(matched_dir, f"matched_page_{page_no}.csv"))

    # Save images with bounding boxes of matched tables
    save_matched_image_with_boxes(input_image, mapping_df, output_dir=drawn_dir)

    # Save matched and unmatched tables as JSON files
    matched = matched_tables.to_dict(orient='records')
    unmatched = unmatched_tables.to_dict(orient='records')
    meta = {
        "file_name": os.path.basename(input_image),
        "page_no": page_no
    }

    data = {
        "matched": matched,
        "unmatched": unmatched,
        "meta": meta
    }

    with open(os.path.join(json_dir, f"page_{page_no}.json"), "w") as json_file:
        json.dump(data, json_file, indent=4)

    return data



###########################################################################################################################
'''                Lists all college folders from S3 and processes each college directory
                   Generates output and uploads to S3   
'''
###########################################################################################################################
def list_college_folders(bucket_name, prefix):
    """ Lists all college folders under the specified prefix in S3. """
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix, Delimiter='/')
    folders = [content['Prefix'] for content in response.get('CommonPrefixes', [])]
    return folders


def process_all_colleges(bucket_name, input_prefix, output_prefix):
    """ Processes all college folders under input_prefix and uploads results to output_prefix on S3. """
    college_folders = list_college_folders(bucket_name, input_prefix)
    for college_folder in college_folders:
        college_name = college_folder.split('/')[-2]  # Extract college name from path
        print(f"Processing {college_name}...")
        logging.info(f"Processing {college_name}...")


        # Paths for input and output
        input_path = os.path.join(input_prefix, college_name)
        output_path = os.path.join(output_prefix, college_name)

        process_college_s3(bucket_name, input_path, output_path)

    print(f"All colleges processed and uploaded to {output_prefix}.")



###########################################################################################################################
'''                Downloads input files from S3, processes them, and uploads the results
                   Handles a single college directory   
'''
###########################################################################################################################
def process_college_s3(bucket_name, input_path, output_path):
    local_dir = 'temp_college'
    os.makedirs(local_dir, exist_ok=True)

    # Step 1: Download input files from S3
    download_from_s3(bucket_name, os.path.join(input_path, 'record-book.pdf'), os.path.join(local_dir, 'record-book.pdf'))
    download_from_s3(bucket_name, os.path.join(input_path, 'unsan.txt'), os.path.join(local_dir, 'unsan.txt'))
    download_from_s3(bucket_name, os.path.join(input_path, 'config.json'), os.path.join(local_dir, 'config.json'))

    # Step 2: Convert PDF to images (pages)
    images_dir = os.path.join(local_dir, 'images')
    os.makedirs(images_dir, exist_ok=True)
    pdf_path = os.path.join(local_dir, 'record-book.pdf')

    convert_pdf_to_images(pdf_path, images_dir)

    # Step 3: Process each image using Textract
    output_dir = os.path.join(local_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)

    for image_file in os.listdir(images_dir):
        image_path = os.path.join(images_dir, image_file)
        process_single_image(
            image_path,
            os.path.join(local_dir, 'unsan.txt'),
            os.path.join(local_dir, 'config.json'),
            output_dir
        )

    for image_file in os.listdir(images_dir):
        local_image_path = os.path.join(images_dir, image_file)
        s3_image_key = os.path.join(output_path, "images", image_file)
        upload_to_s3(local_image_path, bucket_name, s3_image_key)

    # Step 5: Upload output folders (matched_tables_drawn, json_files, dump)
    # upload_to_s3(os.path.join(output_dir, "matched_tables_drawn"), bucket_name, os.path.join(output_path, "matched_tables_drawn"))
    matched_tables_drawn_dir = os.path.join(output_dir, "matched_tables_drawn")
    for file in os.listdir(matched_tables_drawn_dir):
        local_file_path = os.path.join(matched_tables_drawn_dir, file)
        s3_key = os.path.join(output_path, "matched_tables_drawn", file)
        upload_to_s3(local_file_path, bucket_name, s3_key)


    # upload_to_s3(os.path.join(output_dir, "json_files"), bucket_name, os.path.join(output_path, "matched_unmatched_files"))
    json_files_dir = os.path.join(output_dir, "json_files")
    for file in os.listdir(json_files_dir):
        local_file_path = os.path.join(json_files_dir, file)
        s3_key = os.path.join(output_path, "matched_unmatched_files", file)
        upload_to_s3(local_file_path, bucket_name, s3_key)

    
    dump_dir = os.path.join(output_dir, "dump")
    sub_dirs = ["textract_tables", "matched_tables", "unmatched_tables"]

    for sub_dir in sub_dirs:
        sub_dir_path = os.path.join(dump_dir, sub_dir)
        for file in os.listdir(sub_dir_path):
            local_file_path = os.path.join(sub_dir_path, file)
            s3_key = os.path.join(output_path, "dump", sub_dir, file)
            upload_to_s3(local_file_path, bucket_name, s3_key)

    # Step 6: Upload tables_drawn folder to S3
    tables_drawn_dir = os.path.join(output_dir, "tables_drawn")
    for file in os.listdir(tables_drawn_dir):
        local_file_path = os.path.join(tables_drawn_dir, file)
        s3_key = os.path.join(output_path, "all_detected_tables_drawn", file)
        upload_to_s3(local_file_path, bucket_name, s3_key)

    # Step 7: Upload evaluation file directly to the college folder
    upload_to_s3(os.path.join(output_dir, "matching_evaluation.txt"), bucket_name, os.path.join(output_path, "matching_evaluation.txt"))

    print(f"Finished processing {input_path} and uploaded results to {output_path}.")
    logging.info(f"Finished processing {input_path} and uploaded results to {output_path}.")



###########################################################################################################################
'''                Uploads a local file to S3
                   Utility function for S3 upload   
'''
###########################################################################################################################
def upload_to_s3(local_path, bucket_name, s3_key):
    s3_client.upload_file(local_path, bucket_name, s3_key)
    print(f"Uploaded {local_path} to S3 at {s3_key}")
    logging.info(f"Uploaded {local_path} to S3 at {s3_key}")



###########################################################################################################################
'''                Downloads a file from S3
                   Utility function for S3 download   
'''
###########################################################################################################################
def download_from_s3(bucket_name, s3_key, local_path):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    s3_client.download_file(bucket_name, s3_key, local_path)
    print(f"Downloaded {s3_key} to {local_path}")
    logging.info(f"Downloaded {s3_key} to {local_path}")



###########################################################################################################################
'''                Main entry point: Processes all colleges and uploads results
                   Executes when the script is run   
'''
###########################################################################################################################

if __name__ == '__main__':
    bucket_name = 'recordbooks'  # Replace with your bucket name
    input_prefix = 'input-data/'  # Prefix for input folders
    output_prefix = 'output-data/'  # Prefix for output folders

    process_all_colleges(bucket_name, input_prefix, output_prefix)



################################################      END      ############################################################ 