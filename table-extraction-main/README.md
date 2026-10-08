# README

## Master Documentation for Sports Table Extraction and Prediction Pipeline

This repository contains scripts and utilities for sports table data extraction, prediction, and dataset generation. Below is an overview of the key components and their functionality, with links to detailed documentation for each.

### 1. Header Prediction

The **Header Prediction** script uses the OpenAI API to predict and extract sports-related table data from images. It predicts fields such as entity type, stat category, statistic, and stat period based on predefined allowed values.

- **Functionality**:
  - Encodes the image into a base64 format.
  - Sends the image to the OpenAI API with a custom prompt.
  - Extracts sports-related data in JSON format.

For more information, refer to the detailed [Header Prediction README](HEADER_PREDICTION.md).

### 2. Dataset Generation

The **Dataset Generation** script samples sports records from JSON files for specific colleges, copies corresponding images, and creates a new dataset. The result is a folder structure containing sampled images and a `data.json` file with relevant information for each record.

- **Functionality**:
  - Randomly samples sports records from JSONL files for specified colleges.
  - Copies the corresponding images to a target folder.
  - Generates a new `data.json` file containing the sampled records.

For more information, refer to the detailed [Dataset Generation README](GENERATE_DATASET.md).

### 3. Finding Unmatched Tables

The **Unmatched Tables** script processes scanned document images using AWS Textract to extract table data, compares it with a textual reference (unsan file), and identifies unmatched tables. It also visualizes the unmatched tables by drawing bounding boxes on the images.

- **Functionality**:
  - Uses AWS Textract to extract tables from images.
  - Compares extracted tables with ground truth data.
  - Identifies unmatched tables and visualizes them by drawing bounding boxes on the images.

For more information, refer to the detailed [Unmatched Tables README](UNMATCHED_README.md).

---

### How to Use

Each of these scripts has a dedicated purpose within the pipeline, and you can follow their respective documentation to understand the input/output requirements, how to run them, and the expected results.

- To predict headers from images, refer to [Header Prediction README](HEADER_PREDICTION.md).
- To generate a new dataset from JSON files and images, refer to [Dataset Generation README](GENERATE_DATASET.md).
- To find and visualize unmatched tables, refer to [Unmatched Tables README](UNMATCHED_README.md).

This structure provides a complete pipeline from dataset generation, through table extraction, to table prediction and unmatched table detection.