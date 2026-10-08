from transformers import AutoProcessor, AutoModelForObjectDetection
from PIL import Image
import torch
import cv2
import numpy as np

def preprocess_image(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    image = cv2.GaussianBlur(image, (5, 5), 0)
    image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    return image


# Load the fine-tuned table detection model
processor = AutoProcessor.from_pretrained("microsoft/table-transformer-detection")
model = AutoModelForObjectDetection.from_pretrained("microsoft/table-transformer-detection")

# Extract id2label mapping from the model configuration
id2label = model.config.id2label



def detect_tables(image):
    # Convert numpy array to PIL Image
    if isinstance(image, (np.ndarray, np.generic)):
        image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    inputs = processor(images=image, return_tensors="pt")
    outputs = model(**inputs)

    # Extract bounding boxes for tables
    target_sizes = torch.tensor([image.size[::-1]])
    results = processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=0.9)[0]

    table_bboxes = []
    for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
        if id2label[label.item()] == "table":
            table_bboxes.append(box.tolist())
    return table_bboxes


