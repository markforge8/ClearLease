"""
Authentication Utilities
========================
Handles authentication middleware and user verification.
"""

from fastapi import Depends, HTTPException, status
from typing import Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.config.database import get_db
from backend.utils.jwt import verify_access_token
from backend.models.data_models import UserProfile

# Create a security scheme that doesn't raise an error when no token is provided
optional_security = HTTPBearer(auto_error=False)


def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security), db: Session = Depends(get_db)) -> Optional[UserProfile]:
    """
    Get the current authenticated user, or None if not authenticated.
    
    Args:
        credentials: HTTP authorization credentials (optional)
        db: Database session
        
    Returns:
        Optional[UserProfile]: Current authenticated user, or None if not authenticated
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        
        payload = verify_access_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            return None
        
        user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        
        return user
    
    except Exception as e:
        return None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()), db: Session = Depends(get_db)) -> UserProfile:
    """
    Get the current authenticated user.
    
    Args:
        credentials: HTTP authorization credentials
        db: Database session
        
    Returns:
        UserProfile: Current authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    
    try:
        payload = verify_access_token(token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
