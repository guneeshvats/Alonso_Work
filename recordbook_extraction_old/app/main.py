from fastapi import FastAPI, BackgroundTasks
from app.routes import submit_job, job_status
# Results and Logs are removed 

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "The application is running!!"}

# Include routes for different functionalities
app.include_router(submit_job.router)
app.include_router(job_status.router)
# app.include_router(logs.router)
# app.include_router(results.router)
