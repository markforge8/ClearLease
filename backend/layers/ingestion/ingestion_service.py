"""
Ingestion Service
================
This service handles the ingestion layer responsibilities:
- Receiving input text data
- Normalizing text content
- Computing basic text statistics
- Preparing normalized text blocks for the extraction layer

This service implements the ingestion v0 contract with minimal placeholder logic.
No business logic, contract understanding, risk analysis, extraction, or analysis is implemented.
"""

from datetime import datetime
from backend.models.data_models import (
    IngestionInput,
    IngestionResult,
    TextBlock
)


class IngestionService:
    """
    Service class for handling data ingestion v0.
    
    This service defines the contract for ingesting text data and normalizing it
    for downstream processing layers.
    """
    
    def __init__(self):
        """Initialize the ingestion service."""
        pass
    
    def ingest(self, input_data: IngestionInput) -> IngestionResult:
        """
        Main ingestion method that processes input text according to the ingestion v0 contract.
        
        This method:
        1. Validates the input text
        2. Normalizes the text (whitespace normalization, trimming)
        3. Computes basic statistics
        4. Returns normalized text blocks with statistics
        
        Args:
            input_data: IngestionInput containing text content and optional metadata
            
        Returns:
            IngestionResult containing normalized text blocks and statistics
            
        Raises:
            ValueError: If input validation fails
        """
        # Validate input
        self._validate_input(input_data)
        
        # Normalize text and create text blocks
        text_blocks = self._create_text_blocks(input_data.text)
        
        # Compute totals
        total_characters = sum(block.normalized_length for block in text_blocks)
        total_words = sum(block.word_count for block in text_blocks)
        
        # Build metadata
        metadata = {
            "has_source_metadata": input_data.metadata is not None,
            "has_source_id": input_data.source_id is not None,
            "block_count": len(text_blocks)
        }
        if input_data.metadata:
            metadata["source_metadata_keys"] = list(input_data.metadata.keys())
        
        # Build and return result
        return IngestionResult(
            text_blocks=text_blocks,
            source_id=input_data.source_id,
            ingestion_timestamp=datetime.utcnow(),
            total_characters=total_characters,
            total_words=total_words,
            metadata=metadata
        )
    
    def _validate_input(self, input_data: IngestionInput) -> None:
        """
        Validates the ingestion input structure.
        
        Args:
            input_data: Input to validate
            
        Raises:
            ValueError: If validation fails
        """
        if not input_data.text or not input_data.text.strip():
            raise ValueError("Text content cannot be empty")
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalizes text by:
        - Collapsing multiple whitespace characters to single spaces
        - Trimming leading and trailing whitespace
        - Preserving line breaks for structure
        
        Args:
            text: Raw text to normalize
            
        Returns:
            Normalized text string
        """
        # Split by lines to preserve structure
        lines = text.split('\n')
        
        # Normalize each line: collapse whitespace and trim
        normalized_lines = []
        for line in lines:
            # Collapse multiple spaces/tabs to single space
            normalized_line = ' '.join(line.split())
            # Only add non-empty lines
            if normalized_line:
                normalized_lines.append(normalized_line)
        
        # Join lines back with newlines
        return '\n'.join(normalized_lines)
    
    def _count_words(self, text: str) -> int:
        """
        Counts words in text by splitting on whitespace.
        
        Args:
            text: Text to count words in
            
        Returns:
            Word count
        """
        if not text.strip():
            return 0
        return len(text.split())
    
    def _create_text_blocks(self, text: str) -> list[TextBlock]:
        """
        Creates text blocks from input text.
        For v0, creates a single text block containing the entire normalized text.
        
        Args:
            text: Raw text to process
            
        Returns:
            List of TextBlock objects
        """
        # Normalize the text
        normalized_text = self._normalize_text(text)
        
        # Compute statistics
        original_length = len(text)
        normalized_length = len(normalized_text)
        line_count = len(normalized_text.split('\n')) if normalized_text else 1
        word_count = self._count_words(normalized_text)
        
        # Create a single text block for v0
        text_block = TextBlock(
            block_id="block_0",
            order=0,
            normalized_text=normalized_text,
            original_length=original_length,
            normalized_length=normalized_length,
            line_count=line_count,
            word_count=word_count
        )
        
        return [text_block]

