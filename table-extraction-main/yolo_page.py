import cv2
import supervision as sv
from ultralytics import YOLO
import boto3
import pandas as pd
import os
import re
import nltk
import sys
import json
from PIL import Image, ImageDraw
import numpy as np
import typer
import matplotlib.pyplot as plt

model = YOLO('yolov10x_best.pt')

def get_page_number_from_filename(file_path):
    page_no_str = file_path.split('-')[-1].split('.')[0]  # Extract '0001' from '...page-0001.jpg'
    page_no = int(page_no_str)
    return page_no

class TextractProcessor:
    def __init__(self, config):
        self.client = boto3.client('textract', region_name='us-east-1',
                                   aws_access_key_id='AKIAYS2NWWBWNO42MKPP',
                                   aws_secret_access_key='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')

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

def detect_and_crop_tables(file_path):
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

# def detect_and_crop_tables(file_path):
#     image = cv2.imread(file_path)
#     results = model(source=file_path, conf=0.2, iou=0.8)[0]
#     detections = sv.Detections.from_ultralytics(results)

#     table_class_id = 8  # Table class ID is 8
#     cropped_tables = []
#     bbox_coords = []

#     for i, (xyxy, conf, cls_id) in enumerate(zip(detections.xyxy, detections.confidence, detections.class_id)):
#         if cls_id == table_class_id:
#             x1, y1, x2, y2 = map(int, xyxy)
#             cropped_image = image[y1:y2, x1:x2]
#             cropped_tables.append(cropped_image)
#             bbox_coords.append((x1, y1, x2, y2))

#             plt.imshow(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB))
#             plt.title(f"Cropped Table {i+1}")
#             plt.axis('off')
#             plt.show()

#             print(f"Cropped Table {i+1}: Coordinates (x1, y1, x2, y2) = {x1}, {y1}, {x2}, {y2}")
#         else:
#             print(f"Skipping detection {i+1} (not a table).")

#     return cropped_tables, bbox_coords

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
            "table_id": best[2],
            "image_text": best[1],
            "unsan_text": i_tab,
            "bleu_score": best[0],
            "page_no": unsan_page_no,
            "line_no": unsan_line_no
        })

    return mapping

def get_matched_unmatched_tables(df_image, df_unsan, dump_dir, image_name):
    mapping = get_bleu_mapping(df_image, df_unsan)
    mapping_df = pd.DataFrame(mapping)

    mapping_filename = f"Mapping_{image_name}.csv"
    mapping_df.to_csv(os.path.join(dump_dir, mapping_filename), index=False)

    matched_ids = mapping_df['table_id'].tolist()
    matched = df_image[df_image['TableId'].isin(matched_ids)]
    unmatched = df_image[~df_image['TableId'].isin(matched_ids)]

    return matched, unmatched

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
        output_path = os.path.join(output_dir, f"{os.path.splitext(os.path.basename(image_file))[0]}_{table_id}.jpg")
        img_copy.save(output_path, quality=95)

def main(input_image: str, unsan_file: str, config_path: str, output_dir: str):
    tp = TextractProcessor(config=json.loads(open(config_path).read()))
    page_no = get_page_number_from_filename(input_image)
    up = UnsanProcessor(unsan_file, include_pages=[page_no])

    cropped_tables, bbox_coords = detect_and_crop_tables(input_image)

    table_texts = []
    for cropped_image in cropped_tables:
        text = tp.get_text_from_cropped_image(cropped_image)
        table_texts.append(text)

    left_coords = [x1 / Image.open(input_image).width for x1, _, _, _ in bbox_coords]
    top_coords = [y1 / Image.open(input_image).height for _, y1, _, _ in bbox_coords]
    width_coords = [(x2 - x1) / Image.open(input_image).width for x1, _, x2, _ in bbox_coords]
    height_coords = [(y2 - y1) / Image.open(input_image).height for _, y1, _, y2 in bbox_coords]

    df_image = pd.DataFrame({
        'TableId': [f'table_{i+1}' for i in range(len(table_texts))],
        'Text': table_texts,
        'Left': left_coords,
        'Top': top_coords,
        'Width': width_coords,
        'Height': height_coords
    })
    df_image.to_csv(os.path.join(output_dir, "image_tables.csv"))

    df_unsan = up.df
    df_unsan.to_csv(os.path.join(output_dir, "unsan_tables.csv"))

    image_name = os.path.splitext(os.path.basename(input_image))[0]
    matched_tables, unmatched_tables = get_matched_unmatched_tables(df_image, df_unsan, output_dir, image_name)
    unmatched_tables.to_csv(os.path.join(output_dir, "unmatched.csv"))

    draw_bounding_boxes(input_image, matched_tables, output_dir)
    draw_bounding_boxes(input_image, unmatched_tables, output_dir)

if __name__ == '__main__':
    typer.run(main)
