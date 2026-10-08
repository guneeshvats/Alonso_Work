
## Table Matching with Textract and Unsan Processor

This project processes scanned document images using AWS Textract to extract table data, compares it with a textual reference (unsan file), and identifies unmatched tables. It also visualizes the unmatched tables by drawing bounding boxes on the images.

### Requirements

1. **Python 3.x**
2. **AWS Account with Textract service access**
3. **Required Python Libraries**:
   - `boto3`
   - `pandas`
   - `Pillow`
   - `nltk`
   - `typer`

You can install the required dependencies by running:

```bash
pip install boto3 pandas Pillow nltk typer
```

Make sure that AWS credentials are properly configured for Textract to work.

### Project Structure

- **TextractProcessor**: Class responsible for extracting tables from an image using AWS Textract.
- **UnsanProcessor**: Class responsible for processing the unsan file and extracting tables from it.
- **get_bleu_mapping**: Function to compute BLEU score and map tables from the image to the unsan tables.
- **get_unmatched_tables**: Function to identify unmatched tables based on BLEU scores.
- **draw_bounding_boxes**: Function to draw bounding boxes around unmatched tables in the image.
- **main**: Main function that orchestrates the processing of input files, matching tables, and visualization.

### Workflow

1. **Textract Table Extraction**: The `TextractProcessor` extracts tables from an image file by calling AWS Textract's `analyze_document` API.
   
2. **Unsan Table Processing**: The `UnsanProcessor` processes an unsan file, extracting relevant tables and their associated page numbers.

3. **BLEU Matching**: The `get_bleu_mapping` function compares the tables from the image with the unsan tables using the BLEU score to measure the similarity of texts.

4. **Unmatched Tables Identification**: The `get_unmatched_tables` function identifies tables in the image that do not have a close match in the unsan file.

5. **Bounding Box Visualization**: For unmatched tables, bounding boxes are drawn on the image, and the output is saved as an image.

### How to Use

1. **Prepare Input Files**:
   - **Image**: Provide a scanned image of the document in JPG format.
   - **Unsan File**: Provide a text file with table data to compare against.
   - **Config File**: Provide a configuration JSON file with AWS Textract credentials:
     ```json
     {
       "region_name": "<aws-region>",
       "aws_access_key_id": "<your-access-key>",
       "aws_secret_access_key": "<your-secret-key>"
     }
     ```

2. **Run the Script**:

   To run the program, use the following command:

   ```bash
   python <script_name>.py <input_image> <unsan_file> <config_file> <output_directory>
   ```

   Example:

   ```bash
   python textract_processor.py ./images/page-0001.jpg ./unsan_data/unsan.txt ./config/aws_config.json ./output
   ```

### Output

- `image_tables.csv`: A CSV file containing the tables extracted from the image.
- `unsan_tables.csv`: A CSV file containing the tables from the unsan file.
- `unmatched.csv`: A CSV file listing unmatched tables from the image.
- `bb.png`: An image with bounding boxes drawn around unmatched tables.



### BLEU Scoring

The script uses the BLEU score to compare tables extracted from the image and the unsan file. A higher BLEU score indicates greater similarity.

### Error Handling

- If the AWS Textract request fails, check if your AWS credentials and region settings are correct.
- Ensure that the input image file path and unsan file are properly formatted and accessible.

### Notes

- The script assumes that the file name of the image follows a specific pattern, with the page number appearing at the end (e.g., `page-0001.jpg`).
- Make sure to preprocess your unsan file and images if they do not conform to the expected format.
