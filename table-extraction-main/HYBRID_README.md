# Hybrid Table Detection and Analysis System

A robust system for detecting, extracting, and analyzing tables from images using YOLO object detection and AWS Textract. The system can process single images or batch process multiple images, comparing detected tables with reference content from unsanitized text files.

## Features

- 🔍 Table detection using YOLO neural network model
- 📄 Text extraction using AWS Textract
- 🔄 Table matching using BLEU score comparison
- 📦 Support for batch processing of multiple images
- 📊 Generation of detailed analysis reports
- 🎯 High-accuracy table region detection
- 📝 Comprehensive output in JSON format

## Prerequisites

- Python 3.8 or higher
- AWS account with Textract access
- CUDA-capable GPU (recommended for optimal YOLO performance)

## Installation

1. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Download NLTK data:
```python
import nltk
nltk.download('punkt')
```

5. Download the YOLO model:
```bash
# Place your YOLO model file in the /models directory
mkdir models
# Copy your yolov10x_best.pt to the models directory
```

## Configuration

1. Create a configuration file `config.json`:
```json
{
    "region_name": "your-aws-region",
    "aws_access_key_id": "your-access-key",
    "aws_secret_access_key": "your-secret-key"
}
```

2. Set up your directory structure:
```
project_root/
├── images/           # Input images
├── models/           # YOLO model files
│   └── yolov10x_best.pt
├── unsan.txt        # Reference text file
├── output/          # Output directory
└── dump/            # Temporary processing files
```

## Usage

### Single Image Processing

```bash
python get_unmatched_tables_hybrid.py run-image \
    --image-file "path/to/image.jpg" \
    --unsan-file "path/to/unsan.txt" \
    --config-path "path/to/config.json" \
    --output-dir "path/to/output"
```

### Batch Processing

```bash
python get_unmatched_tables_hybrid.py run-all \
    --source-dir "path/to/source/directory" \
    --config-path "path/to/config.json"
```

## Output Format

The system generates JSON output with the following structure:

```json
{
    "matched": [
        {
            "TableId": "table_1",
            "Text": "extracted table text",
            "Left": 0.1,
            "Top": 0.2,
            "Width": 0.3,
            "Height": 0.4,
            "PageNo": 1,
            "unsan_line_no": 10,
            "unsan_text": "reference text",
            "bleu_score": 0.85
        }
    ],
    "unmatched": [...],
    "meta": {
        "file_name": "image.jpg"
    }
}
```

## Directory Structure

```
├── get_unmatched_tables_hybrid.py  # Main entry point
├── requirements.txt                # Package dependencies
├── config.json                     # AWS configuration
├── models/                         # YOLO model directory
├── images/                         # Input images
├── output/                         # Processed results
└── dump/                           # Temporary files
```

## Troubleshooting

1. CUDA Issues:
   - Ensure CUDA toolkit is properly installed
   - Check GPU compatibility
   - Verify CUDA version matches PyTorch requirements

2. AWS Textract Issues:
   - Verify AWS credentials
   - Check IAM permissions
   - Ensure proper region configuration

3. Common Errors:
   - `ModuleNotFoundError`: Run `pip install -r requirements.txt`
   - `InvalidImageFormatError`: Ensure images are in supported format (JPG/PNG)
   - `ResourceNotFoundException`: Check AWS configuration