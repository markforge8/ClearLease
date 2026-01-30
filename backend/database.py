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
    from backend.models.data_models import UserProfile, Payment, AnalysisRecord
    
    # Drop analysis_records table if it exists
    from sqlalchemy import MetaData
    metadata = MetaData()
    metadata.reflect(bind=engine)
    if 'analysis_records' in metadata.tables:
        AnalysisRecord.__table__.drop(bind=engine)
        print("Dropped existing analysis_records table.")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")