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
from ultralytics import YOLO
import supervision as sv
import shutil
import tqdm


# Loading the model
model = YOLO('models/yolov10x_best.pt')
print("Loaded YOLO model")

app = typer.Typer()

def get_page_number_from_filename(file_path):
    page_no_str = file_path.split('-')[-1].split('.')[0]  # Extract '0001' from '...page-0001.jpg'
    page_no = int(page_no_str)
    return page_no

class TextractProcessor:
    def __init__(self, config):
        self.client = boto3.client('textract', region_name=config['region_name'],
                                   aws_access_key_id=config['aws_access_key_id'],
                                   aws_secret_access_key=config['aws_secret_access_key'])

    def get_text_from_cropped_image(self, cropped_image):
        rgb_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)
        _, img_bytes = cv2.imencode('.jpg', rgb_image, [int(cv2.IMWRITE_JPEG_QUALITY), 100])

        response = self.client.analyze_document(
            Document={'Bytes': img_bytes.tobytes()},
            FeatureTypes=['LAYOUT']
        )
        return self.extract_text(response)

    def extract_text(self, response):
        extracted_text = ''
        for block in response['Blocks']:
            if block['BlockType'] == 'LINE':
                extracted_text += block['Text'] + ' '
        return extracted_text.strip()

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



def get_bleu_mapping(df_image, df_unsan):
    mapping = []
    for _, row in df_unsan.iterrows():
        i_tab = row['Table']
        i_tab_s = list(i_tab.lower())
        unsan_page_no = row['PageNo']
        unsan_line_no = row['LineNo']

        best = [0, None, None]
        for _, jrow in df_image.iterrows():
            j_tab = jrow['Text']
            j_tab_s = list(j_tab.lower())

            bleu_score = nltk.translate.bleu_score.sentence_bleu([j_tab_s], i_tab_s)
            if bleu_score > best[0]:
                best[0] = bleu_score
                best[1] = j_tab
                best[2] = jrow["TableId"]

        mapping.append({
            "table_id": best[2] if best[2] is not None else 'unmatched',
            "image_id": best[2],
            "image_text": best[1],
            "unsan_text": i_tab,
            "bleu_score": best[0],
            "page_no": unsan_page_no,
            "line_no": unsan_line_no
        })

    return pd.DataFrame(mapping)


# def get_matched_unmatched_tables(df_image_textract, df_image_yolo, df_unsan, dump_dir, image_name):
#     mapping_textract = get_bleu_mapping(df_image_textract, df_unsan)
#     mapping_yolo = get_bleu_mapping(df_image_yolo, df_unsan)

#     # Add source information to the mapping DataFrames
#     mapping_textract['source'] = 'textract'
#     mapping_yolo['source'] = 'yolo'

#     mapping = []
#     # Handle cases where either mapping might be empty
#     textract_unsan_texts = set(mapping_textract.get('unsan_text', []))
#     yolo_unsan_texts = set(mapping_yolo.get('unsan_text', []))
    
#     combined_unsan_texts = textract_unsan_texts.union(yolo_unsan_texts)

#     for unsan_text in combined_unsan_texts:
#         textract_match = mapping_textract[mapping_textract['unsan_text'] == unsan_text]
#         yolo_match = mapping_yolo[mapping_yolo['unsan_text'] == unsan_text]
        
#         if not textract_match.empty and not yolo_match.empty:
#             if textract_match['bleu_score'].values[0] > yolo_match['bleu_score'].values[0]:
#                 mapping.append(textract_match.iloc[0].to_dict())
#             else:
#                 mapping.append(yolo_match.iloc[0].to_dict())
#         elif not textract_match.empty:
#             mapping.append(textract_match.iloc[0].to_dict())
#         elif not yolo_match.empty:
#             mapping.append(yolo_match.iloc[0].to_dict())

#     mapping_df = pd.DataFrame(mapping) if mapping else pd.DataFrame()

#     # Handle case where no tables are matched
#     if mapping_df.empty:
#         # If no matches, everything is unmatched
#         matched_textract = pd.DataFrame()
#         unmatched_textract = df_image_textract.copy()
#         matched_yolo = pd.DataFrame()
#         unmatched_yolo = df_image_yolo.copy()
#     else:
#         # Find matched and unmatched for both Textract and YOLO
#         matched_textract = df_image_textract[
#             df_image_textract['TableId'].isin(
#                 mapping_df[mapping_df['source'] == 'textract']['table_id']
#             )
#         ]
#         unmatched_textract = df_image_textract[
#             ~df_image_textract['TableId'].isin(
#                 mapping_df[mapping_df['source'] == 'textract']['table_id']
#             )
#         ]
 
#         matched_yolo = df_image_yolo[
#             df_image_yolo['TableId'].isin(
#                 mapping_df[mapping_df['source'] == 'yolo']['table_id']
#             )
#         ]
#         unmatched_yolo = df_image_yolo[
#             ~df_image_yolo['TableId'].isin(
#                 mapping_df[mapping_df['source'] == 'yolo']['table_id']
#             )
#         ]

#     # Combine matched tables
#     matched = pd.concat([matched_textract, matched_yolo])
#     # Combine unmatched tables
#     unmatched = pd.concat([unmatched_textract, unmatched_yolo])

#     return matched, unmatched, mapping_df


def get_matched_unmatched_tables(df_image_textract, df_image_yolo, df_unsan, dump_dir, image_name):
    mapping_textract = get_bleu_mapping(df_image_textract, df_unsan)
    mapping_yolo = get_bleu_mapping(df_image_yolo, df_unsan)

    # Add source information to the mapping DataFrames
    mapping_textract['source'] = 'textract'
    mapping_yolo['source'] = 'yolo'

    mapping = []
    # Handle cases where either mapping might be empty
    textract_unsan_texts = set(mapping_textract.get('unsan_text', []))
    yolo_unsan_texts = set(mapping_yolo.get('unsan_text', []))
    
    combined_unsan_texts = textract_unsan_texts.union(yolo_unsan_texts)

    for unsan_text in combined_unsan_texts:
        textract_match = mapping_textract[mapping_textract['unsan_text'] == unsan_text]
        yolo_match = mapping_yolo[mapping_yolo['unsan_text'] == unsan_text]
        
        if not textract_match.empty and not yolo_match.empty:
            if textract_match['bleu_score'].values[0] > yolo_match['bleu_score'].values[0]:
                best_match = textract_match.iloc[0].to_dict()
                best_match['source'] = 'textract'
            else:
                best_match = yolo_match.iloc[0].to_dict()
                best_match['source'] = 'yolo'
        elif not textract_match.empty:
            best_match = textract_match.iloc[0].to_dict()
            best_match['source'] = 'textract'
        elif not yolo_match.empty:
            best_match = yolo_match.iloc[0].to_dict()
            best_match['source'] = 'yolo'

        # Append coordinates from the selected source
        best_match['Left'] = textract_match['Left'].values[0] if best_match['source'] == 'textract' else yolo_match['Left'].values[0]
        best_match['Top'] = textract_match['Top'].values[0] if best_match['source'] == 'textract' else yolo_match['Top'].values[0]
        best_match['Width'] = textract_match['Width'].values[0] if best_match['source'] == 'textract' else yolo_match['Width'].values[0]
        best_match['Height'] = textract_match['Height'].values[0] if best_match['source'] == 'textract' else yolo_match['Height'].values[0]
        
        mapping.append(best_match)

    mapping_df = pd.DataFrame(mapping) if mapping else pd.DataFrame()

    # Handle case where no tables are matched
    if mapping_df.empty:
        # If no matches, everything is unmatched
        matched_textract = pd.DataFrame()
        unmatched_textract = df_image_textract.copy()
        matched_yolo = pd.DataFrame()
        unmatched_yolo = df_image_yolo.copy()
    else:
        # Find matched and unmatched for both Textract and YOLO
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
    
        matched_yolo = df_image_yolo[
            df_image_yolo['TableId'].isin(
                mapping_df[mapping_df['source'] == 'yolo']['table_id']
            )
        ]
        unmatched_yolo = df_image_yolo[
            ~df_image_yolo['TableId'].isin(
                mapping_df[mapping_df['source'] == 'yolo']['table_id']
            )
        ]

    # Combine matched tables
    matched = pd.concat([matched_textract, matched_yolo])
    # Combine unmatched tables
    unmatched = pd.concat([unmatched_textract, unmatched_yolo])

    return matched, unmatched, mapping_df





############################################################################################################################################
'''                                                      Detecting and Cropping Tables
'''
###########################################################################################################################################

def detect_and_crop_tables(file_path, model):
    image = cv2.imread(file_path)
    results = model(source=file_path, conf=0.2, iou=0.8)[0]
    detections = sv.Detections.from_ultralytics(results)

    table_class_id = 8  # Table class ID is 8
    cropped_tables = []
    bbox_coords = []

    for i, (xyxy, conf, cls_id) in enumerate(zip(detections.xyxy, detections.confidence, detections.class_id)):
        if cls_id == table_class_id:
            x1, y1, x2, y2 = map(int, xyxy)
            cropped_image = image[y1:y2, x1:x2]
            cropped_tables.append(cropped_image)
            bbox_coords.append((x1, y1, x2, y2))
        else:
            print(f"Skipping detection {i} (not a table).")

    return cropped_tables, bbox_coords

# Saving the images with boxes around detected tables
def save_image_with_boxes(image_path, bbox_coords, output_dir="tables_drawn"):
    os.makedirs(output_dir, exist_ok=True)
    image = cv2.imread(image_path)

    for x, y, w, h in bbox_coords:
        start_point = (x, y)
        end_point = (x + w, y + h)
        color = (255, 0 ,0)  # Green color for the bounding box
        thickness = 2
        cv2.rectangle(image, start_point, end_point, color, thickness)

    output_path = os.path.join(output_dir, os.path.basename(image_path))
    cv2.imwrite(output_path, image)


def save_matched_image_with_boxes(image_path, mapping_df, output_dir="matched_tables_drawn"):
    """
    Draws bounding boxes around matched tables using the coordinates from the better BLEU score source.

    Parameters:
    - image_path: str, path to the input image
    - mapping_df: DataFrame, contains matched table information with coordinates and source
    - output_dir: str, directory to save the processed image with matched tables
    """
    if mapping_df.empty:
        print(f"No matched tables found for {image_path}. Skipping...")
        return  # Skip saving if no matched tables

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Load the image using OpenCV
    image = cv2.imread(image_path)

    # Draw bounding boxes using the coordinates in mapping_df
    for _, row in mapping_df.iterrows():
        x = int(row['Left'] * image.shape[1])
        y = int(row['Top'] * image.shape[0])
        w = int(row['Width'] * image.shape[1])
        h = int(row['Height'] * image.shape[0])
        
        start_point = (x, y)
        end_point = (x + w, y + h)
        color = (0, 0, 255)  # Red color for the bounding box
        thickness = 2
        cv2.rectangle(image, start_point, end_point, color, thickness)

    # Save the image with matched tables drawn
    image_name = os.path.basename(image_path)
    output_path = os.path.join(output_dir, image_name)
    cv2.imwrite(output_path, image)
    # print(f"Saved matched tables image for {image_path} at {output_path}")

def draw_bounding_boxes(image_file, matched_tables, output_dir):
    image = Image.open(image_file)
    im_width, im_height = image.size

    for _, row in matched_tables.iterrows():
        img_copy = image.copy()
        draw = ImageDraw.Draw(img_copy)

        left = row['Left'] * im_width
        top = row['Top'] * im_height
        right = left + (row['Width'] * im_width)
        bottom = top + (row['Height'] * im_height)

        draw.rectangle([left, top, right, bottom], outline='red', width=5)

        table_id = row['TableId']
        fname = image_file.split('/')[-1].split('.')[0]
        output_path = os.path.join(output_dir, f"{fname}_{table_id}.jpg")
        img_copy.save(output_path, quality=95)


def evaluate_matching(output_dir, page_no):
    """
    Evaluates the matching accuracy by comparing detected tables with unsan tables.
    
    Parameters:
    - output_dir: str, path to the directory containing output files ('matched.csv', 'unmatched.csv', 'unsan_tables.csv')
    - page_no: int, the page number for which evaluation is being done
    
    Outputs:
    - Writes evaluation metrics to 'matching_evaluation.txt'
    """
    matched_file = os.path.join(output_dir, "matched.csv")
    unmatched_file = os.path.join(output_dir, "unmatched.csv")
    unsan_file = os.path.join(output_dir, "unsan_tables.csv")
    eval_file_path = os.path.join(output_dir, "matching_evaluation.txt")

    # Load the CSV files
    df_matched = pd.read_csv(matched_file)
    df_unmatched = pd.read_csv(unmatched_file)
    df_unsan = pd.read_csv(unsan_file)

    # Calculate metrics
    detected_count = len(df_matched) + len(df_unmatched)
    unsan_count = len(df_unsan)
    matched_count = len(df_matched)
    accuracy = (matched_count / unsan_count) * 100 if unsan_count > 0 else 0

    # Prepare the evaluation output
    evaluation_output = (
        f"Page No: {page_no}\n"
        f"Detected Tables: {detected_count}\n"
        f"Unsan Tables: {unsan_count}\n"
        f"Matched Tables: {matched_count}\n"
        f"Accuracy: {accuracy:.2f}%\n\n"
    )

    # Write evaluation results to file
    with open(eval_file_path, "a") as eval_file:
        eval_file.write(evaluation_output)

    # print(f"Evaluation completed for page {page_no}. Results saved to {eval_file_path}")


############################################################################################################################################
'''                                                     Typer and Deliverable Functions
'''
###########################################################################################################################################

def process_single_image(input_image: str, unsan_file: str, config_path: str, output_dir:str):
    config = json.loads(open(config_path).read())
    #print(config)
    tp = TextractProcessor(config=json.loads(open(config_path).read()))

    page_no = get_page_number_from_filename(input_image)
    up = UnsanProcessor(unsan_file, include_pages=[page_no])

    # Save the image with drawn bounding boxes
    cropped_tables, bbox_coords = detect_and_crop_tables(input_image, model)

    save_image_with_boxes(input_image, bbox_coords, output_dir="tables_drawn")
    
    table_texts = []
    for cropped_image in cropped_tables:
        text = tp.get_text_from_cropped_image(cropped_image)
        table_texts.append(text)
    
    left_coords = [x1 / Image.open(input_image).width for x1, _, _, _ in bbox_coords]
    top_coords = [y1 / Image.open(input_image).height for _, y1, _, _ in bbox_coords]
    width_coords = [(x2 - x1) / Image.open(input_image).width for x1, _, x2, _ in bbox_coords]
    height_coords = [(y2 - y1) / Image.open(input_image).height for _, y1, _, y2 in bbox_coords]
    
    df_image_yolo = pd.DataFrame({
        'TableId': [f'table_{i + 1}' for i in range(len(table_texts))],
        'Text': table_texts,
        'Left': left_coords,
        'Top': top_coords,
        'Width': width_coords,
        'Height': height_coords,
        'PageNo': page_no
    })
    df_image_yolo.to_csv(os.path.join(output_dir, "image_yolo_tables.csv"))
    
    df_image_textract = tp.get_tables_from_image(input_image)
    df_image_textract.to_csv(os.path.join(output_dir, "image_textract_tables.csv"))

   # print(df_image)
    df_unsan = up.df
    df_unsan.to_csv(os.path.join(output_dir, "unsan_tables.csv"))

    image_name = os.path.splitext(os.path.basename(input_image))[0]
    matched_tables, unmatched_tables, mapping_df = get_matched_unmatched_tables(df_image_textract, df_image_yolo, df_unsan, output_dir, image_name)
    
    # Save matched tables image with bounding boxes drawn 
    # save_matched_image_with_boxes(input_image, matched_tables, bbox_coords, output_dir="matched_tables_drawn")

    unmatched_tables.to_csv(os.path.join(output_dir, "unmatched.csv"))
    matched_tables.to_csv(os.path.join(output_dir, "matched.csv"))

    # draw_bounding_boxes(input_image, matched_tables, output_dir)
    evaluate_matching(output_dir, page_no)

    for _, row in matched_tables.iterrows():
        table_id = row['TableId']
        if table_id in mapping_df['table_id'].tolist():
            mtable = mapping_df[mapping_df['table_id'] == table_id]
            matched_tables.loc[matched_tables['TableId'] == table_id, 'unsan_line_no'] = mtable['line_no'].tolist()[0]
            matched_tables.loc[matched_tables['TableId'] == table_id, 'unsan_text'] = \
            mtable['unsan_text'].tolist()[0]
            matched_tables.loc[matched_tables['TableId'] == table_id, 'bleu_score'] = \
                mtable['bleu_score'].tolist()[0]


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


@app.command("run_image")
def run_image(image_file: str, unsan_file: str, config_path: str, output_dir: str):
    data = process_single_image(image_file, unsan_file, config_path, output_dir)
    print(json.dumps(data, indent=4))

@app.command("run_all")
def process_college(source_dir: str, config_path:str):
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