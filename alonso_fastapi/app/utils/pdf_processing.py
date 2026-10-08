import os
import time
import logging
from pdf2image import convert_from_path
from PIL import Image

def convert_pdf_to_images(pdf_path: str, images_dir: str, dpi: int = 300):
    """
    Converts a PDF to images and saves them in the specified directory.

    Args:
        pdf_path (str): Path to the input PDF file.
        images_dir (str): Directory where the images will be saved.
        dpi (int): Resolution for converting PDF pages to images.
    
    Returns:
        List[str]: List of paths to the saved images.
    """
    try:
        os.makedirs(images_dir, exist_ok=True)
        logging.info(f"Converting PDF {pdf_path} to images in {images_dir} with DPI {dpi}")
        
        # Convert PDF pages to images
        pages = convert_from_path(pdf_path, dpi=dpi)
        image_paths = []

        for i, page in enumerate(pages):
            image_path = os.path.join(images_dir, f'page-{i + 1:04d}.png')
            page.save(image_path, 'PNG')
            image_paths.append(image_path)
            logging.info(f"Saved page {i + 1} as {image_path}")
            print(f"Saved page {i + 1} as {image_path}")
            time.sleep(0.1)  # Small delay to ensure proper write 

        return image_paths

    except Exception as e:
        logging.error(f"Failed to convert PDF {pdf_path} to images: {e}")
        raise
