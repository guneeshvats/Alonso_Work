import cv2
import pytesseract

def extract_table_text(image_path, table_bboxes):
    image = cv2.imread(image_path)
    table_texts = []

    for bbox in table_bboxes:
        x1, y1, x2, y2 = map(int, bbox)
        cropped_table = image[y1:y2, x1:x2]
        text = pytesseract.image_to_string(cropped_table, config="--psm 6 --oem 3")
        table_texts.append(text)

    return table_texts
