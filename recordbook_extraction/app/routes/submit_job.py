#############################################################################################################################  
#                                         FASTAPI ROUTES FOR JOB SUBMISSION                                                                                                                                        
#############################################################################################################################

'''
Purpose:
    - Provides API endpoints to submit college processing jobs.
    - Supports processing a single college or an entire folder of colleges.
    - Fetches processing progress from a stored JSON file.

Key Features:
    - Uses Celery to queue jobs for background processing.
    - Leverages AWS Textract for table extraction from PDFs.
    - Retrieves processing status via a progress tracking file.

Created by:
    Guneesh Vats
    ML Engineer, Alonzo

Dated:
    23rd Jan, 2024
    Thursday
'''

#############################################################################################################################
#                                                     IMPORTS                                                                      
#############################################################################################################################

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.celery_worker import process_college, process_folder
from app.utils.s3_utils import list_colleges_in_folder, create_s3_client
import os
import json

#############################################################################################################################
''' 
Define API Router:
    - Registers API endpoints related to job submission.
'''
#############################################################################################################################
router = APIRouter()



#############################################################################################################################
''' 
Define Request Models:
    - `CollegeRequest`: Handles credentials and college-specific processing details.
    - `FolderRequest`: Handles credentials and folder-wide processing details.
'''
#############################################################################################################################
class CollegeRequest(BaseModel):
    s3_access_key: str
    s3_secret_key: str
    s3_region_name: str  
    textract_access_key: str
    textract_secret_key: str
    textract_region_name: str  
    bucket_name: str
    folder_name: str
    college_name: str

class FolderRequest(BaseModel):
    s3_access_key: str
    s3_secret_key: str
    s3_region_name: str  
    textract_access_key: str
    textract_secret_key: str
    textract_region_name: str  
    bucket_name: str
    folder_name: str



#############################################################################################################################
''' 
Submit Job for Single College:
    - Asynchronously queues a job to process one college.
    - Uses Celery to execute tasks in the background.
    
    Endpoint: POST /submit-job/
    
    Request Body:
        - AWS S3 credentials
        - AWS Textract credentials
        - S3 bucket and folder details
        - College name to process
    
    Returns:
        - Job ID and status confirmation.
'''
#############################################################################################################################
@router.post("/submit-job/")
async def submit_job(request: CollegeRequest):
    """
    Submits a job to process a single college.
    """
    task = process_college.apply_async(args=[
        request.s3_access_key, request.s3_secret_key, request.s3_region_name,  
        request.textract_access_key, request.textract_secret_key, request.textract_region_name, 
        request.bucket_name, request.folder_name, request.college_name
    ])
    return {"job_id": task.id, "status": "Job submitted"}



#############################################################################################################################
''' 
Submit Job for Processing an Entire Folder:
    - Lists all colleges inside the specified S3 folder.
    - Submits individual processing jobs for each college.
    - Uses Celery to parallelize job execution.
    
    Endpoint: POST /process-folder/
    
    Request Body:
        - AWS S3 credentials
        - AWS Textract credentials
        - S3 bucket and folder details
    
    Returns:
        - Job IDs and statuses for each college processed.
'''
#############################################################################################################################
@router.post("/process-folder/")
async def process_folder(request: FolderRequest):
    """
    Processes all college folders inside the specified S3 folder.
    """
    #  Create S3 Client (Fixed missing region)
    s3_client = create_s3_client(request.s3_access_key, request.s3_secret_key, request.s3_region_name)

    #  Fetch Colleges from S3
    colleges = list_colleges_in_folder(s3_client, request.bucket_name, request.folder_name)
    
    if not colleges:
        raise HTTPException(status_code=404, detail=f"No colleges found in folder {request.folder_name}")

    results = {}
    for college_name in colleges:
        task = process_college.apply_async(args=[
            request.s3_access_key, request.s3_secret_key, request.s3_region_name, 
            request.textract_access_key, request.textract_secret_key, request.textract_region_name,  
            request.bucket_name, request.folder_name, college_name
        ])
        results[college_name] = {"job_id": task.id, "status": "Job submitted"}

    return {"message": f"Processing all colleges in folder {request.folder_name}", "results": results}



#############################################################################################################################
''' 
Fetch Processing Progress:
    - Reads progress from a JSON file stored in `/tmp1/progress/progress.json`.
    - Returns the current processing status if available.
    
    Endpoint: GET /progress/
    
    Returns:
        - JSON object containing progress details.
        - Error message if progress file is missing or inaccessible.
'''
#############################################################################################################################
@router.get("/progress/")
def get_progress():
    """
    Returns the current progress of the processing.
    """
    PROGRESS_FILE = "/tmp1/progress/progress.json"

    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f) 
        else:
            return {"message": "No processing is currently running"}
        
    except Exception as e:
        return {"error": str(e)}
