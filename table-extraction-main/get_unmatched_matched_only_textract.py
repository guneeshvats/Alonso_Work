##############################################################################################################################
##############################################################################################################################
'''
Purpose : 
This script processes scanned images or PDF pages to extract tabular data using Amazon Textract. It compares the extracted 
tables with reference tables provided in a text file (`unsan.txt`) and evaluates the matching accuracy. Additionally, it 
visualizes the detected tables by drawing bounding boxes on the original images and generates output files summarizing the
results.

Key Features:
1. Extracts tables from images using Amazon Textract.
2. Matches extracted tables with reference tables using BLEU score.
3. Draws bounding boxes around matched tables on images.
4. Saves the detected tables as CSV files.
5. Evaluates detection accuracy by comparing matched and unmatched tables.
6. Supports processing individual images or a directory of images.

Inputs : 
1. `image_file` (str) - Path to the input image to be processed.
2. `unsan_file` (str) - Path to the reference text file (`unsan.txt`) containing known tables for comparison.
3. `config_path` (str) - Path to the JSON configuration file with AWS Textract credentials.
4. `output_dir` (str) - Directory where the output files will be saved.
 

Created By :
    Guneesh Vats
    ML Engineer, Alonzo

Dated : 
    7th Jan, 2024
    Tuesday
'''
##############################################################################################################################
##############################################################################################################################


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

app = typer.Typer()



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

    df_image_textract = tp.get_tables_from_image(input_image)
    df_image_textract.to_csv(os.path.join(output_dir, "image_textract_tables.csv"))

    # Saving and plotting the boundaries of all detected tables for every page
    save_all_detected_tables(input_image, df_image_textract, output_dir="tables_drawn")

    df_unsan = up.df
    df_unsan.to_csv(os.path.join(output_dir, "unsan_tables.csv"))

    image_name = os.path.splitext(os.path.basename(input_image))[0]
    matched_tables, unmatched_tables, mapping_df = get_matched_unmatched_tables(df_image_textract, df_unsan, output_dir, image_name)

    unmatched_tables.to_csv(os.path.join(output_dir, "unmatched.csv"))
    matched_tables.to_csv(os.path.join(output_dir, "matched.csv"))

    # Saving the matched tables 
    save_matched_image_with_boxes(input_image, mapping_df, output_dir="matched_tables_drawn")
    evaluate_matching(output_dir, page_no)

    matched = matched_tables.to_dict(orient='records')
    unmatched = unmatched_tables.to_dict(orient='records')
    meta = {
        "file_name": os.path.basename(input_image),
    }

    data = {
        "matched": matched,
        "unmatched": unmatched,
        "meta": meta
    }

    return data



###########################################################################################################################
'''
Typer Commands : 
run_image - Processes a single image using the process_single_image() function.
run_all - Processes all images in a specified directory.
'''
###########################################################################################################################

@app.command("run_image")
def run_image(image_file: str, unsan_file: str, config_path: str, output_dir: str):
    data = process_single_image(image_file, unsan_file, config_path, output_dir)
    print(json.dumps(data, indent=4))


@app.command("run_all")
def process_college(source_dir: str, config_path: str):
    images_path = os.path.join(source_dir, "images")
    unsan_file = os.path.join(source_dir, "unsan.txt")
    output_dir = os.path.join(source_dir, "output")
    dump_dirs = os.path.join(source_dir, "dump")

    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)

    os.makedirs(output_dir)

    if os.path.exists(dump_dirs):
        shutil.rmtree(dump_dirs)

    os.makedirs(dump_dirs)
    print(f"Total images: {len(os.listdir(images_path))}")

    unable_to_process = []
    for image_file in tqdm.tqdm(os.listdir(images_path)):
        image_file_path = os.path.join(images_path, image_file)
        image_name = image_file.split(".")[0]
        image_dump_dir = os.path.join(dump_dirs, image_name)
        os.makedirs(image_dump_dir)
        try:
            image_out = process_single_image(image_file_path, unsan_file, config_path, image_dump_dir)
            out_file = os.path.join(output_dir, f"{image_name}.json")
            with open(out_file, "w") as f:
                f.write(json.dumps(image_out))
        except Exception as e:
            print(f"Failed to process image {image_file}: {e}")
            unable_to_process.append(image_file)

    print(json.dumps(unable_to_process, indent=4))


if __name__ == '__main__':
    app()
