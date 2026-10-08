from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict

class TeamModel(BaseModel):
    """
    Represents a sports team with its identifying information and visual attributes.
    
    Attributes:
        code (int): Unique identifier code for the team
        name (str): Full official name of the team
        gTeamId (int): Global team identifier used across systems
        tidyName (str): Clean, URL-friendly version of team name
        imgUrl (str): URL to team's logo/image
        colorCode (str): Team's primary color in hex format
    """
    code: int
    name: str
    gTeamId: int
    tidyName: str
    imgUrl: str
    colorCode: str

class SportModel(BaseModel):
    """
    Defines a sport with its basic identifying information.
    
    Attributes:
        name (str): Full name of the sport
        code (str): Unique identifier code for the sport
        gLeagueId (int): Global league identifier for the sport
    """
    name: str
    code: str
    gLeagueId: int

class UserRegister(BaseModel):
    """
    Model for user registration data validation.
    
    Attributes:
        UserName (str): Unique username for the account
        Password (str): User's password (will be hashed before storage)
        Team (Optional[TeamModel]): User's associated team, if any
        Sports (Optional[List[SportModel]]): List of sports the user is associated with
        Email (EmailStr): Valid email address for the user
    """
    UserName: str
    Password: str
    Team: Optional[TeamModel] = None
    Sports: Optional[List[SportModel]] = []
    Email: EmailStr

class UserLogin(BaseModel):
    """
    Model for user login credentials validation.
    
    Attributes:
        UserName (str): User's registered username
        Password (str): User's password for authentication
    """
    UserName: str
    Password: str

class Token(BaseModel):
    """
    Model for JWT token response structure.
    
    Attributes:
        access_token (str): Short-lived JWT token for API access
        refresh_token (str): Long-lived token for obtaining new access tokens
        token_type (str): Type of token (typically "bearer")
    """
    access_token: str
    refresh_token: str
    token_type: str

class UserResponse(BaseModel):
    """
    Model for user data returned after successful operations.
    
    Attributes:
        userid (str): Unique identifier for the user
        username (str): User's registered username
        email (str): User's registered email address
        team (Optional[TeamModel]): User's associated team information
        sports (Optional[List[SportModel]]): List of sports associated with user
    """
    userid: str
    username: str
    email: str
    team: Optional[TeamModel] = None
    sports: Optional[List[SportModel]] = []
