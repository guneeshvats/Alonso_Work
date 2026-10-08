import os
import cv2
import json
import pandas as pd
from PIL import Image, ImageDraw
from ultralytics import YOLO
import typer
import sys

print("Command-line arguments:", sys.argv)

# Loading the model
model = YOLO('models/yolov10x_best.pt')
print("Loaded YOLO model")

app = typer.Typer()

def draw_and_save_bounding_boxes(image_file, bbox_coords, output_dir):
    """
    Draws bounding boxes on the input image and saves the modified image.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    image = Image.open(image_file)
    draw = ImageDraw.Draw(image)

    for x1, y1, x2, y2 in bbox_coords:
        draw.rectangle([x1, y1, x2, y2], outline='red', width=5)

    output_path = os.path.join(output_dir, os.path.basename(image_file))
    image.save(output_path, quality=95)
    print(f"Saved annotated image: {output_path}")

def detect_and_draw_tables(input_image, model, output_dir):
    """
    Detects tables in the input image, draws bounding boxes around them,
    and saves the modified image in the specified output directory.
    """
    # Load the image using OpenCV
    image = cv2.imread(input_image)
    results = model(source=input_image, conf=0.2, iou=0.8)[0]

    # Extract detections
    detections = results.boxes
    bbox_coords = []

    for box in detections:
        x1, y1, x2, y2 = map(int, box.xyxy[0])  # Convert bounding box to integers
        bbox_coords.append((x1, y1, x2, y2))

    # Draw and save the bounding boxes on the image
    draw_and_save_bounding_boxes(input_image, bbox_coords, output_dir)

@app.command()
def detect_tables(
    source_dir: str,
    output_dir: str
):
    """
    Detect tables in images from SOURCE_DIR and save annotated images to OUTPUT_DIR.
    """
    print(f"Source directory: {source_dir}")
    print(f"Output directory: {output_dir}")

    images = [
        os.path.join(source_dir, img)
        for img in os.listdir(source_dir)
        if img.lower().endswith(('.png', '.jpg', '.jpeg'))
    ]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for image_file in images:
        try:
            detect_and_draw_tables(image_file, model, output_dir)
        except Exception as e:
            print(f"Error processing {image_file}: {e}")

if __name__ == "__main__":
    print("Running Typer app")
    app()
