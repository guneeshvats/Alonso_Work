from celery import Celery
from app.utils.s3_utils import download_from_s3, upload_to_s3, list_colleges_in_folder
from app.utils.pdf_processing import convert_pdf_to_images
from app.utils.table_extraction import process_single_image, combine_json_files
from app.utils.progress_tracker import update_progress
import os
import logging

# Initialize Celery with Redis broker and backend
celery_app = Celery(
    "tasks",
    broker="redis://redis:6379/0",  # Redis container URL
    backend="redis://redis:6379/0"
)

# Set Celery configurations
celery_app.conf.update(task_track_started=True)

# Create a global logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Default StreamHandler (logs to console)
    ]
)
logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def upload_logs(self, log_file_path, bucket_name, s3_key):
    """Uploads logs.txt to S3."""
    if os.path.exists(log_file_path):
        upload_to_s3(log_file_path, bucket_name, s3_key)
        logger.info(f"Uploaded logs.txt to S3 at {s3_key}.")


@celery_app.task(bind=True)
def process_college(self, bucket_name: str, college_name: str):
    try:
        # Define local directory structure
        local_dir = f"output-data/{college_name}"
        logs_dir = f"{local_dir}/logs"
        log_file_path = f"{logs_dir}/logs.txt"
        os.makedirs(logs_dir, exist_ok=True)

        # Configure file-based logging dynamically
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(file_handler)

        # Step 1: Download input files
        update_progress(college_name, "Downloading Input Files")
        download_from_s3(bucket_name, f"input-data/{college_name}/record-book.pdf", f"{local_dir}/record-book.pdf")
        download_from_s3(bucket_name, f"input-data/{college_name}/unsan.txt", f"{local_dir}/unsan.txt")
        download_from_s3(bucket_name, f"input-data/{college_name}/config.json", f"{local_dir}/config.json")
        logger.info(f"Downloaded input files for {college_name}.")

        # Step 2: Create required subdirectories
        sub_dirs = [
            "images", "all_tables_drawn", "matched_tables_drawn",
            "matched_unmatched_json_files",
            "CSV_dump/textract_tables",
            "CSV_dump/matched_tables",
            "CSV_dump/unmatched_tables"
        ]
        for sub_dir in sub_dirs:
            os.makedirs(f"{local_dir}/{sub_dir}", exist_ok=True)

        # Step 3: Convert PDF to images
        convert_pdf_to_images(f"{local_dir}/record-book.pdf", f"{local_dir}/images")
        update_progress(college_name, "PDF to Image Conversion")
        logger.info(f"Converted PDF to images in {local_dir}/images.")
        

        # Step 4: Process each image
        total_images = len(os.listdir(f"{local_dir}/images"))
        # for image_file in os.listdir(f"{local_dir}/images"):
        for i, image_file in enumerate(os.listdir(f"{local_dir}/images")):
            image_path = f"{local_dir}/images/{image_file}"
            update_progress(college_name, "Processing Image", images_done=i+1, total_images=total_images)
            process_single_image(
                input_image=image_path,
                unsan_file=f"{local_dir}/unsan.txt",
                config_path=f"{local_dir}/config.json",
                output_dir=local_dir,
                logger=logger
            )
        logger.info(f"Processed all images for {college_name}.")

        # Step 5: Combine JSON files into master_json_file.json
        update_progress(college_name, "Combining JSON Files")
        combine_json_files(f"{local_dir}/matched_unmatched_json_files", f"{local_dir}/master_json_file.json")

        # Upoloading matching_evaluation.txt if it exists
        evaluation_file_path = f"{local_dir}/matching_evaluation.txt"
        if os.path.exists(evaluation_file_path) and os.path.getsize(evaluation_file_path) > 0:
            s3_key = f"output-data/{college_name}/matching_evaluation.txt"
            update_progress(college_name, "Uploading matching_evaluation.txt to S3")
            upload_to_s3(evaluation_file_path, bucket_name, s3_key)
            logger.info(f"Uploaded {evaluation_file_path} to S3 at {s3_key}")
        else:
            logger.warning(f"Skipping upload: {evaluation_file_path} is missing or empty.")

        # Step 6: Upload all files to S3
        for root, _, files in os.walk(local_dir):
            for file in files:
                # Exclude input files from getting uploaded to output folder of s3 bucket
                if file in ["record-book.pdf", "unsan.txt", "config.json"]:
                    logger.info(f"Skipping upload of input file: {file}")
                    continue
                
                local_file_path = os.path.join(root, file)
                s3_key = local_file_path.replace(local_dir, "").lstrip("/")
                update_progress(college_name, "Uploading Results to S3")
                upload_to_s3(local_file_path, bucket_name, f"output-data/{college_name}/{s3_key}")

        logger.info(f"Uploaded all output files for {college_name} to S3.")


        # Final upload of logs
        s3_log_key = f"output-data/{college_name}/logs/logs.txt"
        upload_logs.delay(log_file_path, bucket_name, s3_log_key)
        logger.info(f"Final upload of logs.txt to S3 at {s3_log_key}.")

        update_progress(college_name, "Completed !! Go and Have a Coffee")

        return {"status": "success", "college_name": college_name}

    except Exception as e:
        logger.error(f"Error processing {college_name}: {str(e)}")
        self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(bind=True)
def process_folder(self, bucket_name: str, folder_name: str):
    """Processes all colleges inside a given folder."""
    try:
        colleges = list_colleges_in_folder(bucket_name, folder_name)

        if not colleges:
            logger.warning(f"No colleges found in folder {folder_name}")
            return {"error": f"No colleges found in folder {folder_name}"}

        results = {}
        for college_name in colleges:
            task = process_college.apply_async(args=[bucket_name, college_name])
            results[college_name] = {"task_id": task.id, "status": "processing"}

        return {"message": f"Processing all colleges in folder {folder_name}", "results": results}

    except Exception as e:
        logger.error(f"Error processing folder {folder_name}: {str(e)}")
        return {"error": str(e)}