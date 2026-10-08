# from fastapi import APIRouter
# import os

# router = APIRouter()

# @router.get("/logs/{college_name}")
# async def get_logs(college_name: str):
#     log_path = f"logs/{college_name}.log"
#     if not os.path.exists(log_path):
#         return {"error": "Log file not found"}
#     with open(log_path, "r") as log_file:
#         return {"logs": log_file.read()}
