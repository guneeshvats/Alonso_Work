#####################################################################################################
''' 
Fetch Job Status:
    - Retrieves the current status of a Celery task using its job ID.
    
    Endpoint: GET /job-status/{job_id}
    
    Returns:
        - Job ID and its current execution status (e.g., PENDING, STARTED, SUCCESS, FAILURE).
'''
#####################################################################################################

from fastapi import APIRouter
from app.celery_worker import celery_app

router = APIRouter()

@router.get("/job-status/{job_id}")
async def get_job_status(job_id: str):
    task = celery_app.AsyncResult(job_id)
    return {"job_id": job_id, "status": task.status}
