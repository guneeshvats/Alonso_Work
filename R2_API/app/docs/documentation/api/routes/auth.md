# Documentation for `auth.py`

# Authentication Module for R2 API

## Overview

This Python script is designed to handle user authentication, registration, and token management for a RESTful API. It utilizes JSON Web Tokens (JWT) for secure token-based authentication and bcrypt for hashing passwords. The script provides several endpoints for user registration, login, refreshing tokens, and verifying tokens. This module is implemented using FastAPI, a modern web framework for building APIs with Python.

## Dependencies

- **FastAPI**: A web framework for building APIs with Python.
- **PyMongo**: A Python distribution containing tools for working with MongoDB.
- **Decouple**: A library for handling environment variables.
- **JWT**: A library for creating and verifying JSON Web Tokens.
- **bcrypt**: A library for hashing passwords.
- **Logging**: Python's standard logging library for logging messages.

## Environment Configuration

- **JWT_SECRET**: The secret key used for encoding and decoding JWTs.
- **JWT_ALGORITHM**: The algorithm used for JWT encoding, typically "HS256".
- **ACCESS_TOKEN_EXPIRE_MINUTES**: Duration in minutes after which the access token expires.
- **REFRESH_TOKEN_EXPIRE_DAYS**: Duration in days after which the refresh token expires.

## Database Configuration

The script uses MongoDB to store user data. The database connection is established using the `db` object from `app.db.mongo_connection`, and the user data is stored in the `users` collection.

## Functions and Endpoints

### `create_jwt_token`

```python
def create_jwt_token(data: dict, expires_delta: timedelta = None) -> str
```

- **Purpose**: Generates a JWT access token.
- **Args**:
  - `data`: The payload data to be encoded in the token.
  - `expires_delta`: Optional custom expiration time for the token. If not provided, the default access token expiration time is used.
- **Returns**: An encoded JWT token as a string.

### `create_refresh_token`

```python
def create_refresh_token(data: dict) -> str
```

- **Purpose**: Generates a JWT refresh token with an extended expiration period.
- **Args**:
  - `data`: The payload data to encode in the token.
- **Returns**: An encoded refresh token as a string.

### `register_user`

```python
@router.post("/register", response_model=UserResponse)
async def register_user(user: UserRegister)
```

- **Purpose**: Registers a new user in the system.
- **Args**:
  - `user`: The user registration data, including username, password, email, team, and sports.
- **Returns**: The created user details as a `UserResponse`.
- **Raises**: `HTTPException` if the username already exists.

### `login_user`

```python
@router.post("/login")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends())
```

- **Purpose**: Authenticates a user and generates access and refresh tokens.
- **Args**:
  - `form_data`: The login credentials provided as an `OAuth2PasswordRequestForm`.
- **Returns**: A dictionary containing the access token, refresh token, token type, and user details.
- **Raises**: `HTTPException` if the credentials are invalid.

### `refresh_access_token`

```python
@router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_token: str)
```

- **Purpose**: Generates a new access token using a valid refresh token.
- **Args**:
  - `refresh_token`: A valid refresh token.
- **Returns**: A `Token` object containing the new access token and the existing refresh token.
- **Raises**: `HTTPException` if the refresh token is invalid or expired.

### `verify_token`

```python
def verify_token(token: str = Depends(oauth2_scheme))
```

- **Purpose**: Verifies and decodes a JWT token.
- **Args**:
  - `token`: The JWT token to verify.
- **Returns**: The username extracted from the token payload.
- **Raises**: `HTTPException` if the token is invalid or expired.

## Logging

The script uses Python's built-in logging module to log important information, warnings, and errors. The logging level is set to INFO.

## Conclusion

This script provides a robust solution for managing user authentication in a web application using JWT and bcrypt. The use of FastAPI ensures high performance and ease of development, while MongoDB serves as a flexible and scalable data store for user information.
