"""
Authentication Utilities
========================
Handles authentication middleware and user verification.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.config.database import get_db
from backend.utils.jwt import verify_access_token
from backend.models.data_models import UserProfile

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> UserProfile:
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
