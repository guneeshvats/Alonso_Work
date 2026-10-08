import cv2
import os

def preprocess_image(image_path, output_path):
    # Read the image
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Enhance contrast
    enhanced = cv2.equalizeHist(gray)
    
    # Thresholding to improve OCR
    _, thresh = cv2.threshold(enhanced, 180, 255, cv2.THRESH_BINARY)

    # Save the preprocessed image
    cv2.imwrite(output_path, thresh)

def preprocess_images(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    for file_name in os.listdir(input_dir):
        input_path = os.path.join(input_dir, file_name)
        output_path = os.path.join(output_dir, file_name)
        preprocess_image(input_path, output_path)

if __name__ == "__main__":
    input_dir = 'images/'  # Input folder with images
    output_dir = 'preprocessed_images/'  # Output folder for preprocessed images
    preprocess_images(input_dir, output_dir)
