from app.utils.s3_utils import download_from_s3, upload_to_s3
from app.utils.pdf_processing import convert_pdf_to_images
from app.utils.table_extraction import process_single_image
import os
from app.celery_worker import celery_app

@celery_app.task(bind=True)
def process_college(self, college_name: str):
    try:
        # Download data from S3
        download_from_s3(f"input-data/{college_name}/record-book.pdf", "temp/record-book.pdf")
        download_from_s3(f"input-data/{college_name}/unsan.txt", "temp/unsan.txt")
        download_from_s3(f"input-data/{college_name}/config.json", "temp/config.json")

        # Convert PDF to images
        images_dir = "temp/images"
        os.makedirs(images_dir, exist_ok=True)
        convert_pdf_to_images("temp/record-book.pdf", images_dir)

        # Process each image
        for image_file in os.listdir(images_dir):
            process_single_image(
                os.path.join(images_dir, image_file),
                "temp/unsan.txt",
                "temp/config.json",
                "output"
            )

        # Upload results back to S3
        upload_to_s3("output", f"output-data/{college_name}/results.zip")

        return "Processing completed successfully"

    except Exception as e:
        self.retry(exc=e, countdown=60, max_retries=3)  # Retry on failure
