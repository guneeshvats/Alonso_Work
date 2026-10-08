import os
import glob
import cv2
import supervision as sv
from ultralytics import YOLO
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YOLOModel:
    def __init__(self, model_path: str, confidence: float = 0.2, iou: float = 0.8):
        """
        Initialize YOLO model with given parameters
        
        Args:
            model_path (str): Path to the YOLO model file
            confidence (float): Confidence threshold for detections
            iou (float): IOU threshold for non-maximum suppression
        """
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.iou = iou
        logger.info(f"Initialized YOLO model with confidence={confidence}, iou={iou}")

    def detect_objects(self, image_path: str):
        """
        Detect objects in the image and process all results
        
        Args:
            image_path (str): Path to the input image
            
        Returns:
            sv.Detections: Merged detections from all results
        """
        results = self.model(image_path, conf=self.confidence, iou=self.iou)
        all_detections = []
        
        for i, result in enumerate(results):
            detections = sv.Detections.from_ultralytics(result)
            logger.info(f"Result {i}: Found {len(detections)} total detections")
            all_detections.append(detections)
        
        if len(all_detections) > 1:
            merged_detections = sv.Detections.merge(all_detections)
            logger.info(f"Merged {len(all_detections)} detection sets into {len(merged_detections)} total detections")
            return merged_detections
        else:
            logger.info(f"Returning single detection set with {len(all_detections[0])} detections")
            return all_detections[0]

class ImageProcessor:
    def __init__(self, yolo_model: YOLOModel, output_folder: str, box_color=(255, 0, 0), box_thickness=3):
        """
        Initialize image processor with given parameters
        
        Args:
            yolo_model (YOLOModel): Initialized YOLO model instance
            output_folder (str): Path to save processed images
            box_color (tuple): RGB color for bounding boxes
            box_thickness (int): Thickness of bounding box lines
        """
        self.yolo_model = yolo_model
        self.output_folder = output_folder
        self.box_annotator = sv.BoxAnnotator(thickness=box_thickness, color=sv.Color(*box_color))
        os.makedirs(self.output_folder, exist_ok=True)
        logger.info(f"Initialized ImageProcessor with output folder: {output_folder}")

    def process_images(self, input_folder: str, class_id: int = 8):
        """
        Process all images in the input folder and save annotated results
        
        Args:
            input_folder (str): Path to folder containing input images
            class_id (int): Class ID for tables (default is 8)
        """
        image_files = glob.glob(os.path.join(input_folder, '*.jpg'))
        logger.info(f"Found {len(image_files)} images to process")

        for image_file in image_files:
            logger.info(f"Processing image: {image_file}")
            image = cv2.imread(image_file)
            if image is None:
                logger.error(f"Failed to read image: {image_file}")
                continue

            # Detect objects
            detections = self.yolo_model.detect_objects(image_file)
            
            # Filter for tables
            table_detections = self._filter_detections(detections, class_id)
            logger.info(f"Found {len(table_detections)} tables in {image_file}")
            
            # Log confidence scores for debugging
            if len(table_detections.confidence) > 0:
                logger.debug(f"Table confidence scores: {table_detections.confidence}")

            # Annotate and save
            annotated_image = self.box_annotator.annotate(
                scene=image.copy(), 
                detections=table_detections
            )

            output_file = os.path.join(
                self.output_folder, 
                os.path.basename(image_file).replace('.jpg', '_output.png')
            )
            cv2.imwrite(output_file, annotated_image)
            logger.info(f"Saved annotated image to: {output_file}")

            # Save individual cropped tables
            self._save_cropped_tables(image, table_detections, image_file)

    def _filter_detections(self, detections: sv.Detections, class_id: int):
        """
        Filter detections to keep only tables
        
        Args:
            detections (sv.Detections): All detections
            class_id (int): Class ID for tables
            
        Returns:
            sv.Detections: Filtered detections containing only tables
        """
        mask = detections.class_id == class_id
        filtered = sv.Detections(
            xyxy=detections.xyxy[mask],
            confidence=detections.confidence[mask],
            class_id=detections.class_id[mask]
        )
        logger.info(f"Filtered {len(detections)} detections to {len(filtered)} tables")
        return filtered

    def _save_cropped_tables(self, image, detections: sv.Detections, original_image_path: str):
        """
        Save individual cropped tables from the image
        
        Args:
            image: Original image
            detections (sv.Detections): Table detections
            original_image_path (str): Path to original image for naming
        """
        base_name = os.path.splitext(os.path.basename(original_image_path))[0]
        
        for i, xyxy in enumerate(detections.xyxy):
            x1, y1, x2, y2 = map(int, xyxy)
            cropped_table = image[y1:y2, x1:x2]
            
            crop_filename = os.path.join(
                self.output_folder, 
                f"{base_name}_table_{i}.png"
            )
            cv2.imwrite(crop_filename, cropped_table)
            logger.info(f"Saved cropped table {i} to: {crop_filename}")

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='YOLO Table Detection Script')
    parser.add_argument('--model', type=str, required=True,
                      help='Path to the YOLO model weights file (e.g., yolov8n.pt)')
    parser.add_argument('--input', type=str, required=True,
                      help='Path to input folder containing images')
    parser.add_argument('--output', type=str, required=True,
                      help='Path to output folder for processed images')
    parser.add_argument('--conf', type=float, default=0.2,
                      help='Confidence threshold for detection (default: 0.2)')
    parser.add_argument('--iou', type=float, default=0.8,
                      help='IOU threshold for NMS (default: 0.8)')
    parser.add_argument('--debug', action='store_true',
                      help='Enable debug logging')

    args = parser.parse_args()

    # Set up logging based on debug flag
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level, 
                       format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Validate paths
    if not os.path.exists(args.model):
        logger.error(f"Model file not found: {args.model}")
        exit(1)
    
    if not os.path.exists(args.input):
        logger.error(f"Input folder not found: {args.input}")
        exit(1)

    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)

    try:
        # Initialize model and processor
        logger.info("Initializing YOLO model...")
        yolo_model = YOLOModel(args.model, confidence=args.conf, iou=args.iou)
        
        logger.info("Initializing image processor...")
        processor = ImageProcessor(yolo_model, args.output)
        
        # Process images
        logger.info(f"Processing images from: {args.input}")
        processor.process_images(args.input)
        
        logger.info("Processing completed successfully!")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        exit(1)
