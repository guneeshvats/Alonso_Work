import os
from pdf2image import convert_from_path

def convert_pdf_to_images(pdf_path, output_folder):
    """
    Converts a PDF file into individual images for each page.

    Args:
        pdf_path (str): Path to the input PDF file.
        output_folder (str): Path to the folder where images will be saved.

    Returns:
        List of saved image paths.
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    images = convert_from_path(pdf_path)
    image_paths = []
    
    for i, image in enumerate(images):
        image_path = os.path.join(output_folder, f"page-{i+1:04d}.jpg")
        image.save(image_path, "JPEG")
        image_paths.append(image_path)
    
    print(f"Converted {len(images)} pages from {pdf_path} to images in {output_folder}")
    return image_paths

# Test the function
if __name__ == "__main__":
    pdf_path = "sample.pdf"  # Replace with your PDF path
    output_folder = "output_images"
    convert_pdf_to_images(pdf_path, output_folder)
