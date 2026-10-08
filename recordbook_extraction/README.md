# 📘 RecordBook Extraction Pipeline  
This repository contains a complete pipeline for processing large volumes of PDF images using FastAPI, Celery, and Redis. Tasks are queued via FastAPI endpoints and processed asynchronously using Celery workers. Real-time task monitoring is enabled via Flower.

Tasks are **queued via FastAPI**, processed asynchronously using **Celery workers**, and monitored in real-time using **Flower**.  

## 🔗 Documentation  
Detailed documentation available here: [LINK](https://docs.google.com/document/d/197CDZ0q0iKJaq9HjDxk-6qk7RXLjtawzIwuUkE7oq4E/edit?usp=sharing)  

---

## Project Structure  
```bash
RECORDBOOK_EXTRACTION/
│-- app/
│   ├── routes/                  # FastAPI route handlers
│   │   ├── __init__.py
│   │   ├── job_status.py         # Retrieves job status from Celery
│   │   ├── logs.py               # [REMOVED]
│   │   ├── results.py            # [REMOVED for now]
│   │   ├── submit_job.py         # Handles job submission and progress tracking
│   ├── utils/                    # Utility scripts for processing
│   │   ├── __init__.py
│   │   ├── config_loader.py      # [Optional] Configuration loader
│   │   ├── mongo_utils.py        # MongoDB interactions
│   │   ├── pdf_processing.py     # Converts PDFs to images
│   │   ├── progress_tracker.py   # Tracks and updates processing progress
│   │   ├── s3_utils.py           # S3 interactions (upload/download)
│   │   ├── table_extraction.py   # Handles table extraction from images
│   ├── celery_worker.py          # Celery worker for background jobs
│   ├── main.py                   # FastAPI app entry point
│   ├── tasks.py                   # Celery task definitions
│-- docker/                        # Docker-related files
│   ├── Dockerfile                 # Dockerfile for containerizing the app
│-- athl_meta/                      # [Metadata Directory - Purpose?]
│-- .env                            # Environment variables (ignored in Git)
│-- docker-compose.yml              # Docker services (Web, Redis, MongoDB, Worker, Flower)
│-- FastAPI_pipeline_uml_3.png      # Pipeline UML Diagram
│-- plantuml_code_HLD.puml          # High-Level Design UML Code
│-- plantuml_code_LLD.puml          # Low-Level Design UML Code
│-- HLD_extraction_pipeline.png     # High-Level Design diagram image
│-- LLD_extraction_pipeline.png     # Low-Level Design diagram image
│-- README.md                       # Project Documentation (this file)
│-- requirements.txt                 # Python Dependencies
│-- StageRecords.bson                # MongoDB collection dump (binary)
│-- StageRecords.bson.gz             # Compressed MongoDB dump
```

## Prerequisites
Ensure you have the following installed:

1. **Docker and Docker Compose**
2. **Python 3.10+**
3. **AWS credentials** configured for accessing S3 buckets

## Project Setup
   
### Clone the repository:
```bash
git clone <repository-url>
cd alonso_fastapi
```
### Create a conda environment:
```bash
conda create -n my_project python=3.10
conda activate my_project
```
### Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Pipeline
### 1. Start Redis and Celery Worker (via Docker)
Open a terminal and run:
```bash
docker-compose up --build
```
This will start the following services:

- **Redis** (message broker)
- **Celery Worker** (task processor)
- **Flower** (real-time monitoring dashboard)

### 2. Start the FastAPI Web Server
Open another terminal, activate the virtual environment, and run:
```bash
uvicorn app.main:app --reload
```
The API will be available at http://127.0.0.1:8000.

### 3. API Endpoints
#### Submit a Job
Go to the Swagger UI at http://127.0.0.1:8000/docs.
Use the `/submit-job/` endpoint to submit a job.

**Example request body:**
```json
{
  "s3_access_key": "your_key",
  "s3_secret_key": "your_secret",
  "s3_region_name": "us-east-1",
  "textract_access_key": "your_textract_key",
  "textract_secret_key": "your_textract_secret",
  "textract_region_name": "us-east-1",
  "bucket_name": "recordbooks",
  "folder_name": "input-data",
  "college_name": "college_1"
}
```
Make sure all the fields are correctly input. 
A response with a job ID and status will be returned like this:
```json
{
  "job_id": "abc123",
  "status": "Job submitted"
}
```
Use this `job_id` for monitoring/status endpoint.

#### Process an Entire Folder
Submit a request to process all colleges within a specified folder:
```json
{
  "s3_access_key": "your_key",
  "s3_secret_key": "your_secret",
  "s3_region_name": "us-east-1",
  "textract_access_key": "your_textract_key",
  "textract_secret_key": "your_textract_secret",
  "textract_region_name": "us-east-1",
  "bucket_name": "recordbooks",
  "folder_name": "input-data"
}
```
You can directly pass in the folder name in the specific bucket 
(Assuming the credentials of that account are update in the `docker-compose.yml` file)

#### Monitor Progress
There are 2 ways first one is more elaborate about the state of current the program. 
Check the processing progress:
```bash
curl http://localhost:8000/progress/
```
you will see an output like this

```json
{
    "current_college": "college_1",
    "progress": {
        "college_1": {
            "stage": "BLEU Score Comparison",
            "images_processed": "12/20"
        },
        "college_2": {
            "stage": "PDF to Image Conversion",
            "images_processed": "0/15"
        }
    }
}
```
or you can also - go to `http://localhost:8000/progress/`
this will also show the same output. 

#### Exhaustive Chronological List of Monitoring Steps: 
This is the complete step-by-step progress tracking that the user will see in real-time while processing the folder
```bash
Folder-Level Progress (process_college())
1️. Downloading Input Files 
2. PDF to Image Conversion 
3. Processing Images (X/Y)

Image-Level Progress (process_single_image())
(For each image inside college_name/images/ folder, these steps will repeat:) 
4. Textract Processing 
5. Processing Unsan File 
6. Extracting Headers 
7. BLEU Score Comparison 
8. Saving Results

Finalization Steps (process_college())
9️. Combining JSON Files
10. Uploading Results to S3
```
#### Check Job Status
```bash
curl http://localhost:8000/job-status/{job_id}
```
This returns only one of the 3 tags
- STARTED
- COMPLETED
- RETRY
- FAILED

### 4. Monitor Tasks with Flower
Open the Flower dashboard in your browser:
```bash
http://localhost:5555
```
The Flower interface will show:
- **Task statuses:** pending, completed, failed, or retried
- **Worker statistics and task history**
- **Click on individual tasks** to see detailed logs and execution times.

## Useful Commands for Debugging
### Restarting Services
If you encounter issues or need to restart the services:
Stop all running containers:
```bash
docker-compose down
```
Rebuild and start containers:
```bash
docker-compose up --build
```

### Docker Commands
#### List running containers:
```bash
docker ps
```
#### Access the Celery worker container:
```bash
docker exec -it alonso_fastapi-worker-1 sh
```
#### Ping Redis from within the container (to check connectivity):
```bash
redis-cli -h redis ping
```

## Troubleshooting
### Common Issues
#### Redis connection errors:
Ensure the Redis container is running by checking with `docker ps`.
If Redis is unreachable, restart the containers using:
```bash
docker-compose down && docker-compose up --build
```

#### Task retries due to missing credentials:
Ensure AWS credentials are correctly configured in the environment.

#### PDF processing errors:
Ensure `poppler-utils` is installed in the Celery worker container.
```bash
apt update && apt install -y poppler-utils
```

## Input and Output Directory Structure
### Input Data (Stored in AWS S3: `s3://recordbooks/input-data/`)
```
input-data/
│── college_1/
│   ├── record-book.pdf
│   ├── unsan.txt
│   ├── config.json
│── college_2/
│   ├── record-book.pdf
│   ├── unsan.txt
│   ├── config.json
```

### Output Data (Stored in AWS S3: `s3://recordbooks/output-data/`)
```
output-data/
│── college_1/
│   ├── images/
│   ├── all_tables_drawn/
│   ├── matched_tables_drawn/
│   ├── matched_unmatched_json_files/
│   ├── CSV_dump/
│   │   ├── textract_tables/
│   │   ├── matched_tables/
│   │   ├── unmatched_tables/
│   ├── master_json_file.json
│   ├── merged_json_file.json  # NEW
│   ├── matching_evaluation.txt
```

## Future Enhancements
1. **GET Results route - Download processed JSON files**
2. **Support for GPU-based processing on AWS servers**
3. **Advanced monitoring with Prometheus and Grafana**
4. **Error alerting via email or Slack integrations**


## Last Updated
January 2025
**Now includes MongoDB, merging logic, and updated routes. Let me know if any refinements are needed!** 🚀








