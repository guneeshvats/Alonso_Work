from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.celery_worker import process_college
from app.utils.s3_utils import list_colleges_in_folder
import os
import json
import shutil

router = APIRouter()

# To process single college 
class CollegeRequest(BaseModel):
    college_name: str

# To process whole folder of colleges
class FolderRequest(BaseModel):
    folder_name: str
    bucket_name: str # Allow bucket name from request

@router.post("/submit-job/")
async def submit_job(request: CollegeRequest):
    bucket_name = "recordbooks"  # Replace with your S3 bucket
    task = process_college.apply_async(args=[bucket_name, request.college_name])
    return {"job_id": task.id, "status": "Job submitted"}


@router.post("/process-folder/")
async def process_folder(request: FolderRequest):
    colleges = list_colleges_in_folder(request.bucket_name, request.folder_name)
    
    if not colleges:
        raise HTTPException(status_code=404, detail=f"No colleges found in folder {request.folder_name}")

    results = {}
    for college_name in colleges:
        task = process_college.apply_async(args=[request.bucket_name, college_name])
        results[college_name] = {"job_id": task.id, "status": "Job submitted"}

    return {"message": f"Processing all colleges in folder {request.folder_name}", "results": results}


@router.get("/progress/")
def get_progress():
    """Returns the current progress of the processing."""
    PROGRESS_FILE = "/tmp1/progress/progress.json"

    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, "r") as f:
                return json.load(f) 
        else:
            return {"message": "No processing is currently running"}
        
    except Exception as e:
        return {"error": str(e)}

