#############################################################################################################################  
#                                      FASTAPI APPLICATION ENTRY POINT                                                                                                                                         
#############################################################################################################################

'''
Purpose:
    - Initializes and configures the FastAPI application.
    - Defines the root route for health checks.
    - Includes routers for job submission and status tracking.

Key Features:
    - Uses FastAPI for handling API requests.
    - Supports background task execution.
    - Modular route inclusion for scalability.

Created by:
    Guneesh Vats
    ML Engineer, Alonzo

Dated:
    16th Jan, 2024
    Thursday
'''

#############################################################################################################################
#                                               IMPORTS                                                                      
#############################################################################################################################
from fastapi import FastAPI, BackgroundTasks
from app.routes import submit_job, job_status


#############################################################################################################################
''' 
Initialize FastAPI:
    - Creates an instance of FastAPI as the main application.
    - Provides a structured and scalable API framework.
'''
#############################################################################################################################
app = FastAPI()



#############################################################################################################################
''' 
Root Health Check Endpoint:
    - Confirms that the application is running.
    - Returns a JSON response with a success message.
'''
#############################################################################################################################
@app.get("/")
def read_root():
    return {"message": "The application is running!!"}



#############################################################################################################################
''' 
Include API Routes:
    - Integrates job submission and job status tracking endpoints.
    - Supports modular expansion with additional routes (logs, results, etc.).
'''
#############################################################################################################################
app.include_router(submit_job.router)
app.include_router(job_status.router)
# app.include_router(logs.router)
# app.include_router(results.router)
