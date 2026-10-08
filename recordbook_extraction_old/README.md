# Alonzo FastAPI Pipeline with Celery, Redis, and Flower Monitoring
This repository contains a complete pipeline for processing large volumes of PDF images using FastAPI, Celery, and Redis. Tasks are queued via FastAPI endpoints and processed asynchronously using Celery workers. Real-time task monitoring is enabled via Flower.

Link to a detailed documentation of this project : [LINK](https://docs.google.com/document/d/197CDZ0q0iKJaq9HjDxk-6qk7RXLjtawzIwuUkE7oq4E/edit?usp=sharing)

## Pipeline
![FastAPI_pipeline_uml_3](https://github.com/user-attachments/assets/23a46fee-6b72-4b3b-a020-038cb4dc8c4e)


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
  "college_name": "college_1"
}
```
Make sure the college name is a valid folder name in input-data folder of the s3 bucket 
A response with a job ID and status will be returned:
```json
{
  "job_id": "abc123",
  "status": "Job submitted"
}
```
Use this `job_id` for monitoring endpoint.

#### Process an Entire Folder
Submit a request to process all colleges within a specified folder:
```json
{
  "folder_name": "input-data",
  "bucket_name": "recordbooks"
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

#### Check Job Status
```bash
curl http://localhost:8000/job-status/{job_id}
```
This returns only one of the 3 tags
- STARTED
- COMPLETED
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
│   ├── matching_evaluation.txt
```

## Future Enhancements
1. **GET Results route - can download specific college's output or complete folder**
2. **Support for GPU-based processing on AWS servers**
3. **Advanced monitoring with Prometheus and Grafana**
4. **Error alerting via email or Slack integrations**

