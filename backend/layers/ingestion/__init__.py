"""
Ingestion Layer Package
=======================
This package contains the ingestion layer implementation.

Exports:
    IngestionService: Main service class for data ingestion
    IngestionInput: Input data model for ingestion
    IngestionResult: Output data model from ingestion
    TextBlock: Model representing a normalized text block
"""

from .ingestion_service import IngestionService
from models.data_models import IngestionInput, IngestionResult, TextBlock

__all__ = [
    "IngestionService",
    "IngestionInput",
    "IngestionResult",
    "TextBlock"
]

