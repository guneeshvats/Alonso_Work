# Standard library imports
import os

# Third-party imports
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env file
load_dotenv()

# Internal imports - Route handlers and authentication
from app.api.routes import search, auth
from app.api.routes.auth import verify_token
from app.api.routes.search import router as search_router, public_router as search_public_router
from app.api.routes.player_dashboard import router as player_dashboard_router
from app.api.routes.report import router as report_router

# Initialize FastAPI application with metadata
app = FastAPI(title="R2 Search API", version="1.0")

# Configure CORS (Cross-Origin Resource Sharing) allowed origins
# This is necessary to allow frontend applications to communicate with the API
origins = [
    "http://localhost:3000",      # Local development React server
    "http://127.0.0.1:3000"       # Alternative local development URL
]

# Add CORS middleware to allow cross-origin requests
# This configuration allows:
# - Requests from specified origins
# - Credentials in requests
# - All HTTP methods
# - All HTTP headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Testing ...")

# Register route handlers with their respective prefixes and tags
# Auth routes - Handle user authentication and authorization
app.include_router(auth.router, prefix="/auth", tags=["Auth"])

# Protected search routes - Require valid authentication token
app.include_router(search_router, prefix="/api", tags=["Search"], dependencies=[Depends(verify_token)])

# Report routes - No authentication required
app.include_router(report_router, prefix="/api", tags=["Report"])

# Player dashboard routes - Protected routes
app.include_router(player_dashboard_router, prefix="/api", tags=["Player Dashboard"])


# Public search routes - No authentication required
app.include_router(search_public_router, prefix="/api", tags=["Search"])

# Define root endpoint that serves as a basic health check and welcome message
@app.get("/")
def home():
    return {"message": "Welcome to R2 API"}
