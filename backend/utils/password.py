"""
Password Utilities
=================
Handles password hashing and verification using bcrypt.
"""

import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        str: Hashed password
    """
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
    return password_hash.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password to verify
        password_hash: Hashed password to verify against
        
    Returns:
        bool: True if password matches hash, False otherwise
    """
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
