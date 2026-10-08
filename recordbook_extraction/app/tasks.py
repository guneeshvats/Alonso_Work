#############################################################################################################################  
#                                     CELERY TASKS FOR COLLEGE RECORD PROCESSING                                                                                                                                           
#############################################################################################################################

'''
Purpose:
    - Manages the extraction and processing of college record books.
    - Uses AWS S3 for downloading/uploading files.
    - Uses AWS Textract for table extraction from PDF images.
    - Processes each image and stores results in S3.

Key Features:
    - Downloads input files from S3.
    - Converts PDF to images.
    - Extracts tables from images using AWS Textract.
    - Uploads processed data back to S3.
    - Supports Celery task retry on failures.

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

from app.utils.s3_utils import download_from_s3, upload_to_s3, create_s3_client
from app.utils.pdf_processing import convert_pdf_to_images
from app.utils.table_extraction import process_single_image
import os
import boto3
from app.celery_worker import celery_app

#############################################################################################################################
''' 
Initialize Celery Task:
    - Defines a Celery task to process college record books.
    - Uses S3 for file storage and Textract for data extraction.
    - Ensures each college’s data is processed independently.
'''
#############################################################################################################################
@celery_app.task(bind=True)
def process_college(self, s3_access_key, s3_secret_key, s3_region_name, textract_access_key, textract_secret_key, textract_region_name, bucket_name, folder_name, college_name_folder):
    try:
        #  Initialize S3 client with user-provided credentials and region
        s3_client = create_s3_client(s3_access_key, s3_secret_key, s3_region_name)

        #  Define paths
        local_base_path = f"/tmp/{college_name_folder}"
        os.makedirs(local_base_path, exist_ok=True)



        #####################################################################################################
        '''
        Download Input Files
            - Retrieves `record-book.pdf`, `unsan.txt`, and `config.json` from S3 bucket.
            - Saves them to a temporary local directory.
        '''
        #####################################################################################################
        download_from_s3(s3_client, bucket_name, f"{folder_name}/{college_name_folder}/record-book.pdf", f"{local_base_path}/record-book.pdf")
        download_from_s3(s3_client, bucket_name, f"{folder_name}/{college_name_folder}/unsan.txt", f"{local_base_path}/unsan.txt")
        download_from_s3(s3_client, bucket_name, f"{folder_name}/{college_name_folder}/config.json", f"{local_base_path}/config.json")



        #####################################################################################################
        ''' 
        Convert PDF to Images:
            - Converts the downloaded `record-book.pdf` into individual images.
            - Saves images in a dedicated directory for further processing.
        '''
        #####################################################################################################
        images_dir = f"{local_base_path}/images"
        os.makedirs(images_dir, exist_ok=True)
        convert_pdf_to_images(f"{local_base_path}/record-book.pdf", images_dir)



        #####################################################################################################
        ''' 
        Extract Tables from Images:
            - Initializes AWS Textract client.
            - Processes each image using `process_single_image()`.
            - Extracts tabular data and stores output locally.
        '''
        #####################################################################################################
        textract_client = boto3.client(
            "textract",
            region_name=textract_region_name,
            aws_access_key_id=textract_access_key,
            aws_secret_access_key=textract_secret_key
        )
        #  Process each image using Textract
        for image_file in os.listdir(images_dir):
            process_single_image(
                textract_client,
                os.path.join(images_dir, image_file),
                f"{local_base_path}/unsan.txt",
                f"{local_base_path}/config.json",
                f"{local_base_path}/output"
            )



        #####################################################################################################
        ''' 
        Upload Processed Data to S3:
            - Compresses processed output.
            - Uploads the results back to an S3 bucket for further use.
        '''
        #####################################################################################################
        upload_to_s3(s3_client, f"{local_base_path}/output", bucket_name, f"output-data/{college_name_folder}/results.zip")
        return "Processing completed successfully"



    #####################################################################################################
        ''' 
        Error Handling and Retry Mechanism:
            - Implements Celery’s automatic retry on failure.
            - Waits 60 seconds before retrying.
            - Allows up to 3 retries before marking as failed.
        '''
    #####################################################################################################
    except Exception as e:
        self.retry(exc=e, countdown=60, max_retries=3)  # Retry on failure
