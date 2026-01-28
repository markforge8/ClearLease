"""
JWT Utilities
============
Handles JWT token generation and verification.
"""

import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get JWT secret from environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 7


def create_access_token(data: dict) -> str:
    """
    Create a new access token.
    
    Args:
        data: Dictionary to encode in the token
        
    Returns:
        str: Encoded JWT token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> dict:
    """
    Verify an access token and return its payload.
    
    Args:
        token: JWT token to verify
        
    Returns:
        dict: Decoded token payload
        
    Raises:
        JWTError: If token is invalid or expired
    """
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    return payload
