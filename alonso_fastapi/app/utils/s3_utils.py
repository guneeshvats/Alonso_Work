import os
import boto3
import logging
from botocore.exceptions import NoCredentialsError
import shutil


# Initialize the S3 client
s3_client = boto3.client("s3")

def upload_to_s3(local_path: str, bucket_name: str, s3_key: str):
    """
    Uploads a file from the local filesystem to an S3 bucket.
    
    Args:
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

def download_from_s3(bucket_name: str, s3_key: str, local_path: str):
    """
    Downloads a file from an S3 bucket to the local filesystem.
    
    Args:
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

def list_s3_files(bucket_name: str, prefix: str):
    """
    Lists all files in an S3 bucket under a given prefix.
    
    Args:
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

def get_s3_presigned_url(bucket_name: str, object_key: str, expiration: int = 3600) -> str:
    """
    Generate a presigned URL to download an object from S3.
    
    Args:
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
    

def list_colleges_in_folder(bucket_name: str, folder_name: str):
    """
    Lists all college names inside a given folder in the S3 bucket.

    Args:
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