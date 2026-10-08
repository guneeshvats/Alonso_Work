from pytesseract import image_to_string
from PIL import Image
import glob
import os
from tqdm import tqdm 

def ocr_images(input_folder, output_folder):
    """
    Performs OCR on images in the input folder and saves the extracted text in the output folder.

    Parameters:
        input_folder (str): Path to the folder containing images.
        output_folder (str): Path to the folder for saving OCR text files.

    Returns:
        None
    """
    # Ensure output directory exists
    os.makedirs(output_folder, exist_ok=True)
    
    image_files = sorted(glob.glob(f"{input_folder}/*.png"))  # Get all image files
    for image_file in tqdm(image_files, desc="Performing OCR"):
        try:
            img = Image.open(image_file)
            text = image_to_string(img)
            
            # Save OCR result to text file
            output_file = os.path.join(output_folder, os.path.basename(image_file).replace(".png", ".txt"))
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            print(f"Error processing file {image_file}: {e}")
            continue

    print(f"OCR completed. Text files saved in folder: {output_folder}")

# Perform OCR on the output images
ocr_images("output_images", "ocr_output")
