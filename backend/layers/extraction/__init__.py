"""
Extraction Layer Package
========================
This package contains the extraction layer implementation.

Exports:
    ExtractionService: Main service class for data extraction
    ExtractionCandidate: Model representing an extraction candidate result
"""

from .extraction_service import ExtractionService
from models.data_models import ExtractionCandidate

__all__ = [
    "ExtractionService",
    "ExtractionCandidate"
]

