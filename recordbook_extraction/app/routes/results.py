# from fastapi import APIRouter, HTTPException
# from app.utils.s3_utils import get_s3_presigned_url

# router = APIRouter()

# @router.get("/results/{college_name}")
# async def get_results(college_name: str):
#     try:
#         url = get_s3_presigned_url(f"output-data/{college_name}/results.zip")
#         return {"download_link": url}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
