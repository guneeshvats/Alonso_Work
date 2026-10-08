#############################################################################################################################  
#                                   CELERY WORKER FOR AUTOMATED TABLE EXTRACTION                                                                                                                                           
#############################################################################################################################

'''
Purpose:
    - This script defines Celery tasks for extracting tables from PDFs.
    - Handles downloading files, processing PDFs, extracting tables, and merging results with MongoDB.
    - Uses AWS Textract for OCR-based table extraction.
    - Stores processed data in JSON and uploads results to S3.

Key Features:
    - Uses Celery for parallel task execution.
    - Extracts structured tables from PDF images.
    - Matches extracted tables with MongoDB records.
    - Saves and uploads final results, including logs and merged JSON files.

Created by:
    Guneesh Vats
    ML Engineer, Alonzo

Dated:
    23rd Jan, 2024
    Thursday
'''

#############################################################################################################################
#                                               IMPORTS                                                                                                                                              
#############################################################################################################################


from celery import Celery
from app.utils.s3_utils import download_from_s3, upload_to_s3, list_colleges_in_folder, create_s3_client
from app.utils.pdf_processing import convert_pdf_to_images
from app.utils.table_extraction import process_single_image, combine_json_files
from app.utils.progress_tracker import update_progress
import os
import logging
import boto3
from app.utils.table_extraction import merge_with_mongo


#############################################################################################################################
''' 
Celery Configuration:
    - Initializes a Celery worker with Redis as the broker and backend.
    - Limits concurrency to prevent excessive memory usage.
    - Enables tracking of task start times.
'''
#############################################################################################################################
celery_app = Celery(
    "tasks",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)

# Set worker concurrency to prevent memory overload
celery_app.conf.worker_concurrency = 1  

# Set Celery configurations
celery_app.conf.update(task_track_started=True)



#####################################################################################################
''' 
upload_logs():
    - Uploads logs.txt to an S3 bucket.
    - Uses dynamically provided AWS credentials.
'''
#####################################################################################################
# Create a global logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def upload_logs(self, s3_access_key, s3_secret_key, s3_region_name, log_file_path, bucket_name, s3_key):
    """
    Uploads logs.txt to S3 with user-provided credentials.
    """
    try:
        # nitialize S3 Client with user credentials
        s3_client = create_s3_client(s3_access_key, s3_secret_key, s3_region_name)
        
        # Pass the S3 client when calling upload_to_s3
        upload_to_s3(s3_client, log_file_path, bucket_name, s3_key)
        logger.info(f"Uploaded logs.txt to S3 at {s3_key}.")
    except Exception as e:
        logger.error(f"Failed to upload logs.txt to S3: {str(e)}")



#############################################################################################################################
''' 
process_college():
    - Processes a single college's record book:
        1. Downloads necessary files from S3.
        2. Converts PDF to images.
        3. Extracts tables using AWS Textract.
        4. Matches extracted tables with reference data.
        5. Saves matched/unmatched tables and evaluation results.
        6. Merges extracted tables with MongoDB records.
        7. Uploads final results to S3.
'''
#############################################################################################################################
@celery_app.task(bind=True)
def process_college(self, s3_access_key, s3_secret_key, s3_region_name, textract_access_key, textract_secret_key, textract_region_name, bucket_name, folder_name, college_name):
    try:
        #  Initialize S3 Client with user-provided credentials
        s3_client = create_s3_client(s3_access_key, s3_secret_key, s3_region_name)

        #  Initialize Textract Client with user-provided credentials
        textract_client = boto3.client(
            "textract",
            region_name=textract_region_name,
            aws_access_key_id=textract_access_key,
            aws_secret_access_key=textract_secret_key
        )

        #  Define local directory structure
        local_dir = f"output-data/{college_name}"
        logs_dir = f"{local_dir}/logs"
        log_file_path = f"{logs_dir}/logs.txt"
        os.makedirs(logs_dir, exist_ok=True)

        #  Configure file-based logging dynamically
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(file_handler)

        #  Step 1: Download input files
        update_progress(college_name, "Downloading Input Files")
        download_from_s3(s3_client, bucket_name, f"{folder_name}/{college_name}/record-book.pdf", f"{local_dir}/record-book.pdf")
        download_from_s3(s3_client, bucket_name, f"{folder_name}/{college_name}/unsan.txt", f"{local_dir}/unsan.txt")
        download_from_s3(s3_client, bucket_name, f"{folder_name}/{college_name}/config.json", f"{local_dir}/config.json")
        logger.info(f" Downloaded input files for {college_name}.")

        #  Step 2: Create required subdirectories
        sub_dirs = [
            "images", "all_tables_drawn", "matched_tables_drawn",
            "matched_unmatched_json_files",
            "CSV_dump/textract_tables",
            "CSV_dump/matched_tables",
            "CSV_dump/unmatched_tables"
        ]
        for sub_dir in sub_dirs:
            os.makedirs(f"{local_dir}/{sub_dir}", exist_ok=True)

        #  Step 3: Convert PDF to images
        convert_pdf_to_images(f"{local_dir}/record-book.pdf", f"{local_dir}/images")
        update_progress(college_name, "PDF to Image Conversion")
        logger.info(f" Converted PDF to images in {local_dir}/images.")

        #  Step 4: Process each image
        total_images = len(os.listdir(f"{local_dir}/images"))
        for i, image_file in enumerate(os.listdir(f"{local_dir}/images")):
            image_path = f"{local_dir}/images/{image_file}"
            update_progress(college_name, "Processing Image", images_done=i+1, total_images=total_images)
            process_single_image(
                input_image=image_path,
                unsan_file=f"{local_dir}/unsan.txt",
                output_dir=local_dir,
                textract_client=textract_client,
                logger=logger
            )
        logger.info(f" Processed all images for {college_name}.")

        #  Step 5: Combine JSON files into master_json_file.json
        update_progress(college_name, "Combining JSON Files")
        combine_json_files(f"{local_dir}/matched_unmatched_json_files", f"{local_dir}/master_json_file.json")

        # Ensure master_json_file.json exists before merging
        if not os.path.exists(f"{local_dir}/master_json_file.json"):
            logger.error(f" ERROR: Master JSON file missing! Check JSON combination step.")
            return {"status": "error", "message": "Master JSON file missing."}
        
    
        #  Step 6: Upload results back to S3
        for root, _, files in os.walk(local_dir):
            for file in files:
                if file in ["record-book.pdf", "unsan.txt", "config.json"]:
                    continue
                
                local_file_path = os.path.join(root, file)
                s3_key = local_file_path.replace(local_dir, "").lstrip("/")
                update_progress(college_name, "Uploading Results to S3")
                upload_to_s3(s3_client, local_file_path, bucket_name, f"output-data/{college_name}/{s3_key}")

        logger.info(f" Uploaded all output files for {college_name} to S3.")

        #  Final upload of logs
        s3_log_key = f"output-data/{college_name}/logs/logs.txt"
        upload_logs.delay(s3_access_key, s3_secret_key, s3_region_name, log_file_path, bucket_name, s3_log_key)
        logger.info(f" Final upload of logs.txt to S3 at {s3_log_key}.")

        # Merge MongoDB data with master_json.json
        # print("🔍 Calling merge_with_mongo()...")  # Debug
        try:
            merged_json_path = merge_with_mongo()
            if not merged_json_path:
                logger.error(" merge_with_mongo() returned None! Check why MongoDB lookup is failing.")
                return {"status": "error", "message": "MongoDB merge failed."}
        except Exception as e:
            logger.error(f" ERROR: Unexpected issue in merging: {str(e)}")
            return {"status": "error", "message": str(e)}

        if merged_json_path and os.path.exists(merged_json_path):
            s3_merged_key = f"output-data/{college_name}/FINAL_MERGED_JSON.json"
            print(f" Uploading {merged_json_path} to S3 as {s3_merged_key}")  # Debug
            upload_to_s3(s3_client, merged_json_path, bucket_name, s3_merged_key)
            logger.info(f" Uploaded merged JSON to S3 at {s3_merged_key}")
        else:
            print(f" ERROR: Merged JSON missing! Check merging process.")  # Debug
            logger.error(f" ERROR: Merged JSON missing! Check merging process.")

        update_progress(college_name, " Completed !! Go and Have a Coffee ☕")
        return {"status": "success", "college_name": college_name}

    except Exception as e:
        logger.error(f"Error processing {college_name}: {str(e)}")
        self.retry(exc=e, countdown=60, max_retries=3)



#############################################################################################################################
''' 
process_folder():
    - Iterates over all colleges in a given S3 folder.
    - Calls `process_college` asynchronously for each college.
    - Tracks task IDs for monitoring progress.
'''
#############################################################################################################################
@celery_app.task(bind=True)
def process_folder(self, s3_access_key, s3_secret_key, s3_region_name, textract_access_key, textract_secret_key, textract_region_name, bucket_name, folder_name):
    """
    Processes all colleges inside a given folder with user-provided AWS credentials.
    """
    try:
        
        #  Initialize S3 Client with user-provided credentials
        s3_client = create_s3_client(s3_access_key, s3_secret_key, s3_region_name)

        #  List all colleges in the folder
        colleges = list_colleges_in_folder(s3_client, bucket_name, folder_name)

        if not colleges:
            return {"error": f"No colleges found in folder {folder_name}"}

        results = {}
        for college_name in colleges:
            task = process_college.apply_async(args=[
                s3_access_key, s3_secret_key, s3_region_name,
                textract_access_key, textract_secret_key, textract_region_name,
                bucket_name, folder_name, college_name
            ])
            results[college_name] = {"task_id": task.id, "status": "processing"}

        return {"message": f"Processing all colleges in folder {folder_name}", "results": results}

    except Exception as e:
        logger.error(f"Error processing folder {folder_name}: {str(e)}")
        return {"error": str(e)}


