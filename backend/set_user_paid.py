"""
Set user paid status for testing purposes.
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.database import get_db
from models.data_models import UserProfile
from datetime import datetime

# Get database session
db = next(get_db())

# Find test user
user = db.query(UserProfile).filter(UserProfile.email == "test2@example.com").first()

if user:
    # Set user to paid
    user.paid = True
    user.paid_at = datetime.utcnow()
    db.commit()
    print(f"User {user.email} has been set to paid status.")
else:
    print("Test user not found.")
