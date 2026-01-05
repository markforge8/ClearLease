"""
Explanation Service V1
======================
This service handles the explanation layer responsibilities for v1:
- Loading explanation templates from v1 configuration
- Mapping risk_fields to structural risk explanations
- Producing explanations organized by RiskAxis and intensity
- Focusing on "why it's unfair" rather than restating contract terms

This service implements the explanation v1 contract as a pure presentation layer.
No AI, LLM, inference, or template modification is performed.
"""

import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from models.data_models import (
    RiskField,
    RiskFieldExplanation,
    ExplanationOutputV1,
    RiskAxis
)


class ExplainV1Service:
    """
    Service class for handling structural risk field explanations v1.
    
    This service defines the contract for converting risk_fields
    into user-facing structural risk explanations using template-based mapping.
    """
    
    def __init__(self, templates_path: Optional[str] = None):
        """
        Initialize the explanation v1 service.
        
        Args:
            templates_path: Optional path to explanation templates JSON file. If not provided, uses default.
        """
        if templates_path is None:
            # Default to explanation_templates_v1.json in the copy directory
            current_dir = Path(__file__).parent
            templates_path = str(current_dir / "copy" / "explanation_templates_v1.json")
        
        self.templates_path = templates_path
        self.templates: Dict[str, Any] = {}
        self._load_templates()
    
    def _load_templates(self) -> None:
        """
        Load explanation templates from JSON file.
        
        Raises:
            FileNotFoundError: If templates file does not exist
            ValueError: If templates file is invalid
        """
        if not os.path.exists(self.templates_path):
            raise FileNotFoundError(f"Explanation templates file not found: {self.templates_path}")
        
        try:
            with open(self.templates_path, 'r', encoding='utf-8') as f:
                self.templates = json.load(f)
            
            # Validate template structure
            if 'templates' not in self.templates:
                raise ValueError("Templates file must contain 'templates'")
            
            templates = self.templates['templates']
            
            # Validate that all RiskAxis values are present
            expected_axes = ['temporal', 'responsibility', 'liability']
            for axis in expected_axes:
                if axis not in templates:
                    raise ValueError(f"Templates must contain '{axis}' axis")
            
            # Validate that each axis has low, medium, high intensities
            for axis in expected_axes:
                axis_templates = templates[axis]
                for intensity in ['low', 'medium', 'high']:
                    if intensity not in axis_templates:
                        raise ValueError(f"Templates for '{axis}' must contain '{intensity}' intensity")
                    
                    # Validate template structure
                    template = axis_templates[intensity]
                    required_fields = ['title', 'message', 'user_action']
                    for field in required_fields:
                        if field not in template:
                            raise ValueError(f"Template for '{axis}'/{intensity} must contain '{field}'")
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in templates file: {e}")
    
    def explain(self, risk_fields: List[RiskField]) -> ExplanationOutputV1:
        """
        Convert risk_fields into structural risk explanations.
        
        This method:
        1. Maps each risk_field to an explanation using templates based on axis + intensity
        2. Returns empty list if risk_fields is empty
        3. Gracefully skips risk_fields with unknown axis or intensity combinations
        
        Args:
            risk_fields: List of RiskField objects from analysis layer
            
        Returns:
            ExplanationOutputV1 containing list of risk_field_explanations
        """
        # Return empty list if no risk fields
        if not risk_fields:
            return ExplanationOutputV1(risk_field_explanations=[])
        
        risk_field_explanations: List[RiskFieldExplanation] = []
        templates = self.templates.get('templates', {})
        
        for risk_field in risk_fields:
            axis_str = risk_field.axis.value
            intensity = risk_field.intensity
            
            # Check if template exists for this axis and intensity
            if axis_str not in templates:
                # Gracefully skip unknown axis
                continue
            
            axis_templates = templates[axis_str]
            if intensity not in axis_templates:
                # Gracefully skip unknown intensity
                continue
            
            template = axis_templates[intensity]
            
            # Create risk field explanation
            explanation = RiskFieldExplanation(
                axis=risk_field.axis,
                intensity=risk_field.intensity,
                affected_party=risk_field.affected_party,
                title=template['title'],
                message=template['message'],
                user_action=template['user_action'],
                compounding=risk_field.compounding,
                source_blocks=risk_field.source_blocks
            )
            
            risk_field_explanations.append(explanation)
        
        return ExplanationOutputV1(risk_field_explanations=risk_field_explanations)

