
from app.models.issue_models import ReportIssuesRequest, ReportIssuesResponse
from app.api.routes.auth import verify_token 
from fastapi import APIRouter, HTTPException, Depends
from app.services.mail_service import send_email
from datetime import datetime
import logging

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/report-issue", response_model=ReportIssuesResponse)
async def report_issues(request: ReportIssuesRequest, username: str = Depends(verify_token)):
    """
    Protected endpoint for reporting issues with search results.
    
    This endpoint allows users to report issues with search results, which are then
    processed and logged for further analysis.
    
    Args:
        request (ReportIssuesRequest): Contains the issue description and search query
        username (str): Authenticated username from JWT token
        
    Returns:
        ReportIssuesResponse: Contains a success message
        
    Raises:
        HTTPException: For various error conditions with appropriate status codes
    """
    try:
        logger.info(f"User '{username}' is reporting an issue.")
        # logger.info(f"Received report request: {request.dict()}")
        

        logger.error(f"Issue reported by '{username}': {request.Issue}")


        body = f"""
        Issue reported by '{username}': {request.Issue} on {datetime.now()}

        Search Query: {request.SearchQuery}
        AQL Output: {request.aql_output}
        SQL Query: {request.sql_query}
        Inference Time: {request.inference_time}
        Positions: {request.positions}
        Classes: {request.classes}
        Teams: {request.teams}
        
        """


        confirmation = send_email(
            to_email="ganesh@alonzoai.in",
            subject="Issue Report",
            body=body
        )
        
        if confirmation["status"] != "success":
            raise HTTPException(status_code=500, detail="Failed to send email")
        
        return ReportIssuesResponse(Message="Issue reported successfully.")

    except Exception as e:
        # logger.error(f"Error in report_issues: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")