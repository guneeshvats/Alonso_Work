#################################################################################################
#################################################################################################
'''
    Converts a PDF file into images, saving each page as an image in the specified output folder.

    Parameters:
        pdf_path (str): Path to the input PDF file.
        output_folder (str): Path to the output folder for saving images.
        dpi (int): DPI for the conversion (default: 300).  ---- custom resolution

    Returns:
        None
'''
#################################################################################################
#################################################################################################

import os
from pdf2image import convert_from_path
from tqdm import tqdm  
from datetime import datetime

def pdf_to_images(pdf_path, output_folder, dpi=300):
    # Ensure unique output folder with timestamp to avoid overwriting 
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = f"{output_folder}_{timestamp}"
    os.makedirs(output_folder, exist_ok=True)
    
    try:
        images = convert_from_path(pdf_path, dpi=dpi)  
    except Exception as e:
        print(f"Error converting PDF: {e}")
        return

    with tqdm(total=len(images), desc="Converting PDF to images") as pbar:
        for i, image in enumerate(images):
            image.save(f"{output_folder}/page_{i + 1}.png", "PNG")
            pbar.update(1)  

    print(f"PDF converted to images in folder: {output_folder}")

pdf_to_images("ark.pdf", "output_images", dpi=300)
