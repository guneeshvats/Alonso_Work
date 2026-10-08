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



# def zip_and_upload(bucket_name: str, folder_path: str, zip_name: str):
#     """Zips a local folder and uploads it to S3."""
#     if not os.path.exists(folder_path):
#         logging.error(f"Local directory not found: {folder_path}")
#         raise FileNotFoundError(f"Local directory not found: {folder_path}")

#     zip_path = f"{zip_name}.zip"
#     shutil.make_archive(zip_name, "zip", folder_path)

#     s3_client.upload_file(zip_path, bucket_name, f"{zip_name}.zip")
#     os.remove(zip_path)  # Cleanup after upload

#     logging.info(f"Uploaded ZIP: {zip_name}.zip to S3")

#     return f"{zip_name}.zip"


# def zip_and_upload_college(bucket_name: str, college_name: str):
#     """
#     Creates a ZIP file of a college's output data and uploads it to S3.

#     Args:
#         bucket_name (str): The S3 bucket name.
#         college_name (str): The college name (folder inside 'output-data').

#     Returns:
#         str: Presigned URL to download the ZIP file.
#     """
#     try:
#         local_zip_path = f"/tmp/{college_name}.zip"
#         s3_zip_key = f"output-data/{college_name}.zip"

#         # Ensure the folder exists locally
#         local_college_path = f"output-data/{college_name}"
#         if not os.path.exists(local_college_path):
#             raise FileNotFoundError(f"Local directory not found: {local_college_path}")

#         # Create ZIP file
#         shutil.make_archive(local_zip_path.replace(".zip", ""), 'zip', local_college_path)
#         logging.info(f"Created ZIP archive: {local_zip_path}")

#         # Upload ZIP to S3
#         upload_to_s3(local_zip_path, bucket_name, s3_zip_key)
#         logging.info(f"Uploaded ZIP to S3 at: {s3_zip_key}")

#         # Generate presigned URL
#         return get_s3_presigned_url(bucket_name, s3_zip_key)
    
#     except Exception as e:
#         logging.error(f"Error zipping and uploading {college_name}: {e}")
#         return None
    


# def zip_and_upload_full_output(bucket_name: str):
#     """
#     Creates a ZIP of the entire 'output-data' folder and uploads it to S3.

#     Args:
#         bucket_name (str): The S3 bucket name.

#     Returns:
#         str: Presigned URL to download the full ZIP.
#     """
#     try:
#         local_zip_path = "/tmp/output-data.zip"
#         s3_zip_key = "output-data/output-data.zip"

#         if not os.path.exists("output-data"):
#             raise FileNotFoundError("Local 'output-data' directory not found.")

#         # Create ZIP
#         shutil.make_archive(local_zip_path.replace(".zip", ""), 'zip', "output-data")
#         logging.info(f"Created ZIP archive: {local_zip_path}")

#         # Upload to S3
#         upload_to_s3(local_zip_path, bucket_name, s3_zip_key)
#         logging.info(f"Uploaded full output-data ZIP to S3 at: {s3_zip_key}")

#         # Return presigned URL
#         return get_s3_presigned_url(bucket_name, s3_zip_key)

#     except Exception as e:
#         logging.error(f"Error zipping and uploading full output-data: {e}")
#         return None



# def download_folder_from_s3(bucket_name: str, s3_folder: str, local_dir: str):
#     """
#     Downloads all files from an S3 folder to a local directory.
    
#     Args:
#         bucket_name (str): The S3 bucket name.
#         s3_folder (str): The S3 folder key (prefix).
#         local_dir (str): The local directory to save files.
#     """
#     try:
#         os.makedirs(local_dir, exist_ok=True)
#         response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=s3_folder)

#         if "Contents" not in response:
#             raise FileNotFoundError(f"No files found in S3 folder: {s3_folder}")

#         for obj in response["Contents"]:
#             s3_file_path = obj["Key"]
#             relative_path = s3_file_path.replace(s3_folder, "").lstrip("/")
#             local_file_path = os.path.join(local_dir, relative_path)

#             if not s3_file_path.endswith("/"):  # Skip directories
#                 os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
#                 s3_client.download_file(bucket_name, s3_file_path, local_file_path)
#                 logging.info(f"Downloaded {s3_file_path} to {local_file_path}")

#         logging.info(f"Downloaded entire folder {s3_folder} to {local_dir}")

#     except Exception as e:
#         logging.error(f"Failed to download folder {s3_folder} from S3: {e}")
#         raise


# def generate_s3_presigned_url(bucket_name: str, s3_folder: str, expiration: int = 3600):
#     """
#     Generates a presigned URL to download a ZIP archive of an existing S3 folder.

#     Args:
#         bucket_name (str): The S3 bucket name.
#         s3_folder (str): The S3 folder path in the bucket.
#         expiration (int): Expiration time (in seconds) for the URL.

#     Returns:
#         str: A presigned URL if the zip file exists, else None.
#     """
#     try:
#         # Ensure the zip file exists on S3
#         s3_zip_key = f"{s3_folder.rstrip('/')}.zip"  # Assuming it is stored as a ZIP file in S3
#         s3_client.head_object(Bucket=bucket_name, Key=s3_zip_key)  # Check if it exists

#         # Generate presigned URL
#         url = s3_client.generate_presigned_url(
#             "get_object",
#             Params={"Bucket": bucket_name, "Key": s3_zip_key},
#             ExpiresIn=expiration
#         )
#         return url
#     except s3_client.exceptions.ClientError as e:
#         if e.response["Error"]["Code"] == "404":
#             print(f"Error: {s3_zip_key} does not exist in S3.")
#             return None
#         raise
#     except NoCredentialsError:
#         raise RuntimeError("AWS credentials not found. Please configure them.")
    

# def generate_s3_presigned_url_full_output(bucket_name: str, expiration: int = 3600):
#     """
#     Generates a presigned URL to download the full 'output-data.zip' if it exists in S3.

#     Args:
#         bucket_name (str): The S3 bucket name.
#         expiration (int): Expiration time (in seconds) for the URL.

#     Returns:
#         str: A presigned URL if the ZIP file exists, else None.
#     """
#     try:
#         s3_zip_key = "output-data/output-data.zip"  # Full output-data ZIP in S3
#         s3_client.head_object(Bucket=bucket_name, Key=s3_zip_key)  # Check if ZIP exists

#         # Generate pre-signed URL
#         url = s3_client.generate_presigned_url(
#             "get_object",
#             Params={"Bucket": bucket_name, "Key": s3_zip_key},
#             ExpiresIn=expiration
#         )
#         return url
#     except s3_client.exceptions.ClientError as e:
#         if e.response["Error"]["Code"] == "404":
#             print(f"Error: {s3_zip_key} does not exist in S3.")
#             return None
#         raise
#     except NoCredentialsError:
#         raise RuntimeError("AWS credentials not found. Please configure them.")
