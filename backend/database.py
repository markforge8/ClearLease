"""
Database Initialization
=======================
Handles database table creation and initialization.
"""

from sqlalchemy.ext.declarative import declarative_base
from backend.config.database import engine

# Create Base class for models
Base = declarative_base()


def init_db():
    """
    Initialize the database by creating all tables.
    """
    # Import all models here to ensure they are registered with Base
    from backend.models.data_models import UserProfile
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")