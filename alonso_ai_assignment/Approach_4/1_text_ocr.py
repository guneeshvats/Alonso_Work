#################################################################################################
#################################################################################################
'''
    Extracts text from images in the specified folder and saves each as a .txt file.

    Parameters:
        image_folder (str): Path to the folder containing the images.
        output_folder (str): Path to the folder to save text outputs.

    Returns:
        None
'''
#################################################################################################
################################################################################################# 

import pytesseract
from PIL import Image
import os

def extract_text_from_images(image_folder, output_folder):

    os.makedirs(output_folder, exist_ok=True)
    image_files = sorted([f for f in os.listdir(image_folder) if f.endswith('.png')])

    for idx, image_file in enumerate(image_files):
        try:
            image_path = os.path.join(image_folder, image_file)
            output_text_path = os.path.join(output_folder, f"{os.path.splitext(image_file)[0]}.txt")
            
            # Opens the image and apply OCR
            img = Image.open(image_path)
            extracted_text = pytesseract.image_to_string(img)

            # Save the extracted text to a file
            with open(output_text_path, "w") as text_file:
                text_file.write(extracted_text)

            print(f"Processed {image_file} -> {output_text_path}")
        except Exception as e:
            print(f"Error processing {image_file}: {e}")

image_folder = "images"  
output_folder = "text_outputs" 

extract_text_from_images(image_folder, output_folder)
