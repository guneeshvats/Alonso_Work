from yolov5 import detect
import os

def detect_tables(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    detect.run(weights='yolov5s.pt',  # Pretrained YOLOv5 model
               source=input_dir,
               project=output_dir,
               name='results',
               save_txt=True,  # Save detections in .txt format
               save_crop=True)  # Save cropped tables

if __name__ == "__main__":
    input_dir = 'preprocessed_images/'  # Folder with preprocessed images
    output_dir = 'results/'  # YOLO detection results
    detect_tables(input_dir, output_dir)
