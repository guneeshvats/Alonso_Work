#############################################################################################################################  
#                                     AWS S3 UTILITIES FOR FILE MANAGEMENT                                                                                                                                          #############################################################################################
#############################################################################################################################

'''
Purpose:
    - Handles all interactions with AWS S3.
    - Supports file uploads, downloads, listing, and presigned URL generation.
    - Used for processing college records stored in S3.

Key Features:
    - Secure connection to S3 with user-provided credentials.
    - Uploads processed data to S3.
    - Downloads required input files from S3.
    - Lists files and college names from S3 storage.
    - Generates presigned URLs for file access.

Created by:
    Guneesh Vats
    ML Engineer, Alonzo

Dated:
    23rd Jan, 2024
    Thursday
'''

#############################################################################################################################
#                                                          IMPORTS                                                           
#############################################################################################################################
import os
import boto3
import logging
from botocore.exceptions import NoCredentialsError


#############################################################################################################################
''' 
Create S3 Client:
    - Establishes a connection to AWS S3.
    - Requires AWS access key, secret key, and region.
    - Returns an S3 client for performing operations.
'''
#############################################################################################################################
def create_s3_client(access_key: str, secret_key: str, s3_region_name: str):
    return boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=s3_region_name 
    )



#############################################################################################################################
''' 
Upload File to S3:
    - Transfers a file from the local filesystem to an S3 bucket.
    - Uses `s3_client.upload_file()`.
    - Logs success or failure.
'''
#############################################################################################################################
def upload_to_s3(s3_client, local_path: str, bucket_name: str, s3_key: str):
    """
    Args:
        s3_client (boto3.client): Pre-authenticated S3 client.
        local_path (str): Path to the local file.
        bucket_name (str): Name of the S3 bucket.
        s3_key (str): Key (path) under which the file will be stored in S3.
    """
    try:
        s3_client.upload_file(local_path, bucket_name, s3_key)
        logging.info(f"Uploaded {local_path} to S3 at {s3_key}")
        print(f"Uploaded {local_path} to S3 at {s3_key}")
    except Exception as e:
        logging.error(f"Failed to upload {local_path} to S3: {e}")
        raise



#############################################################################################################################
''' 
Download File from S3:
    - Retrieves a file from an S3 bucket and saves it locally.
    - Ensures the local directory exists before downloading.
    - Uses `s3_client.download_file()`.
'''
#############################################################################################################################
def download_from_s3(s3_client, bucket_name: str, s3_key: str, local_path: str):
    """
    Args:
        s3_client (boto3.client): Pre-authenticated S3 client.
        bucket_name (str): Name of the S3 bucket.
        s3_key (str): Key (path) of the file in S3.
        local_path (str): Path where the file will be saved locally.
    """
    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        s3_client.download_file(bucket_name, s3_key, local_path)
        logging.info(f"Downloaded {s3_key} from S3 to {local_path}")
        print(f"Downloaded {s3_key} from S3 to {local_path}")
    except Exception as e:
        logging.error(f"Failed to download {s3_key} from S3: {e}")
        raise



#############################################################################################################################
''' 
List Files in S3:
    - Retrieves all files under a given prefix (folder).
    - Returns a list of file paths (S3 keys).
    - Useful for identifying available college data in S3.
'''
#############################################################################################################################
def list_s3_files(s3_client, bucket_name: str, prefix: str):
    """
    Args:
        s3_client (boto3.client): Pre-authenticated S3 client.
        bucket_name (str): Name of the S3 bucket.
        prefix (str): Prefix (folder path) to search within the bucket.

    Returns:
        List[str]: List of S3 keys (file paths) under the specified prefix.
    """
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        files = [content['Key'] for content in response.get('Contents', [])]
        logging.info(f"Listed {len(files)} files from S3 prefix {prefix}")
        return files
    except Exception as e:
        logging.error(f"Failed to list files in S3 bucket {bucket_name} with prefix {prefix}: {e}")
        raise



#############################################################################################################################
''' 
Generate Presigned URL:
    - Creates a temporary, shareable download link for an S3 object.
    - Allows access without exposing AWS credentials.
    - The URL expires after the specified duration.
'''
#############################################################################################################################
def get_s3_presigned_url(s3_client, bucket_name: str, object_key: str, expiration: int = 3600) -> str:
    """
    Args:
        s3_client (boto3.client): Pre-authenticated S3 client.
        bucket_name (str): The name of the S3 bucket.
        object_key (str): The key of the object in the bucket.
        expiration (int): Time in seconds for the presigned URL to remain valid.

    Returns:
        str: The presigned URL.
    """
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=expiration
        )
        return url
    except NoCredentialsError:
        raise RuntimeError("AWS credentials not found. Please configure them.")



#############################################################################################################################
''' 
List Colleges in Folder:
    - Extracts college names from a specific S3 folder.
    - Uses `CommonPrefixes` to identify unique college directories.
    - Returns a list of college names.
'''
#############################################################################################################################
def list_colleges_in_folder(s3_client, bucket_name: str, folder_name: str):
    """
   Args:
        s3_client (boto3.client): Pre-authenticated S3 client.
        bucket_name (str): Name of the S3 bucket.
        folder_name (str): Name of the folder containing colleges (e.g., 'some_folder/').

    Returns:
        List[str]: A list of college names inside the specified folder.
    """
    try:
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=f"{folder_name}/", Delimiter="/")
        
        # Extract folder names (colleges)
        colleges = [prefix["Prefix"].strip("/").split("/")[-1] for prefix in response.get("CommonPrefixes", [])]
        
        logging.info(f"Found {len(colleges)} colleges in folder {folder_name}: {colleges}")
        return colleges
    except Exception as e:
        logging.error(f"Failed to list colleges in folder {folder_name} in bucket {bucket_name}: {e}")
        return []
