"""
Authentication Module for R2 API

This module handles user authentication, registration, and token management.
It provides endpoints for user registration, login, token refresh, and token verification.
Uses JWT for token-based authentication and bcrypt for password hashing.
"""

import os
import jwt
import bcrypt
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pymongo import MongoClient
from decouple import config
from app.models.auth_models import Token, UserRegister, UserResponse, UserLogin
from app.db.mongo_connection import db
from app.constants import UserDataAuthentication

# Environment Configuration
# -----------------------
# JWT configuration settings loaded from environment variables
JWT_SECRET = config("SECRET_KEY", default="your_secret_key")
JWT_ALGORITHM = config("JWT_ALGORITHM", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(config("ACCESS_TOKEN_EXPIRE_MINUTES", default=30))
REFRESH_TOKEN_EXPIRE_DAYS = int(config("REFRESH_TOKEN_EXPIRE_DAYS", default=7))


# Database Configuration
# --------------------
user_collection = db["users"]  # MongoDB collection for user data

# Authentication Setup
# ------------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # OAuth2 password bearer scheme

# Logging Configuration
# -------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Router Configuration
# ------------------
router = APIRouter()

def create_jwt_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Generate a JWT access token.
    
    Args:
        data (dict): Payload data to encode in the token
        expires_delta (timedelta, optional): Custom expiration time. Defaults to ACCESS_TOKEN_EXPIRE_MINUTES
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """
    Generate a JWT refresh token with extended expiration.
    
    Args:
        data (dict): Payload data to encode in the token
        
    Returns:
        str: Encoded refresh token
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    data.update({"exp": expire})
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserRegister):
    """
    Register a new user in the system.
    
    Args:
        user (UserRegister): User registration data including username, password, email, team, and sports
        
    Returns:
        UserResponse: Created user details
        
    Raises:
        HTTPException: If username already exists
    """
    existing_user = user_collection.find_one({UserDataAuthentication.USERNAME.value: user.UserName})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    # Hash password before storing
    hashed_password = bcrypt.hashpw(user.Password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    print(user.Sports)

    # Prepare user data for storage
    user_data = {
        UserDataAuthentication.EMAIL.value: user.Email,
        UserDataAuthentication.TEAM.value: user.Team.dict() if user.Team else None, 
        UserDataAuthentication.SPORTS.value: [sport.dict() for sport in user.Sports],  
        UserDataAuthentication.USERNAME.value: user.UserName,
        UserDataAuthentication.ISACTIVE.value: True,
        UserDataAuthentication.HASHEDPWD.value: hashed_password,
        UserDataAuthentication.TERMSAGREED.value: False
    }
    print(user_data)
    user_id = str(user_collection.insert_one(user_data).inserted_id)

    return {
        UserDataAuthentication.USERID.value: user_id,
        UserDataAuthentication.USERNAME.value: user.UserName,
        UserDataAuthentication.EMAIL.value: user.Email,
        UserDataAuthentication.TEAM.value: user.Team,
        UserDataAuthentication.SPORTS.value: user.Sports,
        UserDataAuthentication.TERMSAGREED.value: False
    }

@router.post("/login")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and generate access/refresh tokens.
    
    Args:
        form_data (OAuth2PasswordRequestForm): Login credentials
        
    Returns:
        dict: Access token, refresh token, and user details
        
    Raises:
        HTTPException: If credentials are invalid
    """
    user = user_collection.find_one({UserDataAuthentication.USERNAME.value: form_data.username, "isActive": True})
    
    if not user or not bcrypt.checkpw(form_data.password.encode("utf-8"), user[UserDataAuthentication.HASHEDPWD.value].encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Generate tokens
    access_token = create_jwt_token({"sub": user[UserDataAuthentication.USERNAME.value]})
    refresh_token = create_refresh_token({"sub": user[UserDataAuthentication.USERNAME.value]})
    terms_agreed = user.get(UserDataAuthentication.TERMSAGREED.value, False)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "email": user.get(UserDataAuthentication.EMAIL.value, ""),
        "username": user.get(UserDataAuthentication.USERNAME.value, ""),
        "team": user.get(UserDataAuthentication.TEAM.value, {}),
        "sports": user.get(UserDataAuthentication.SPORTS.value, []),
        "terms_agreed": terms_agreed
    }


@router.get("/terms_agreed")
async def terms_agreed(token: str = Depends(oauth2_scheme)):
    try:
        username = verify_token(token)
        user_collection.update_one({UserDataAuthentication.USERNAME.value: username}, {"$set": {UserDataAuthentication.TERMSAGREED.value: True}})
        return {UserDataAuthentication.TERMSAGREED.value: True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_token: str):
    """
    Generate new access token using refresh token.
    
    Args:
        refresh_token (str): Valid refresh token
        
    Returns:
        Token: New access token and existing refresh token
        
    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    try:
        payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        new_access_token = create_jwt_token({"sub": payload["sub"]})
        return {UserDataAuthentication.ACCESSTOKEN.value: new_access_token, UserDataAuthentication.REFRESHTOKEN.value: refresh_token, UserDataAuthentication.TOKENTYPE.value: UserDataAuthentication.BEARER.value}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.get("/verify")
def verify_token(token: str = Depends(oauth2_scheme)):
    """
    Verify and decode JWT token.
    
    Args:
        token (str): JWT token to verify
        
    Returns:
        str: Username from token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        logger.debug("Token decoded. Payload: %s", payload)
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        logger.error("Invalid token: %s", str(e))
        raise HTTPException(status_code=401, detail="Invalid token")
