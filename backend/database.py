"""
Database Initialization
=======================
Handles database table creation and initialization.
"""

from backend.config.database import engine, Base


def init_db():
    """
    Initialize the database by creating all tables.
    """
    # Import all models here to ensure they are registered with Base
    from backend.models.data_models import UserProfile, AnalysisDraft, Payment, AnalysisResult
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")