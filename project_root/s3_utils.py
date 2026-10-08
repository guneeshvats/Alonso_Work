########################################################################################################################
########################################################################################################################
'''
Purpose : This file will contain helper functions to interact with S3 for downloading and uploading files.


Created By : 
    Guneesh Vats

Dated : 
    8th Jan, 2025
    Wednesday
'''
########################################################################################################################
########################################################################################################################
import boto3
import os

s3 = boto3.client('s3')

def download_from_s3(bucket_name, key, local_path):
    """
    Download a file from S3.
    """
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    s3.download_file(bucket_name, key, local_path)

def upload_to_s3(bucket_name, key, local_path):
    """
    Upload a file to S3.
    """
    s3.upload_file(local_path, bucket_name, key)


