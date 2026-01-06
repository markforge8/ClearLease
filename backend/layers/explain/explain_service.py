"""
Explanation Service v0 (FREE)
=============================
This service handles the explanation layer responsibilities for FREE tier:
- Loading explanation templates from configuration
- Mapping AnalysisOutput to user-facing explanations
- Producing explanation blocks for each risk item

This service implements the explanation v0 contract as a pure presentation layer.
No AI, LLM, inference, risk analysis, or template modification is performed.

IMPORTANT: explain v0 = FREE tier
- Only provides factual explanations
- No conclusion-type information
- No action recommendations
- No "should you sign"暗示

Why can't merge with v1:
- v0 is designed for FREE access with minimal functionality
- v1 is for PAID tier with structured next-step guidance
- Business model requires clear separation between free and paid features
"""

import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from backend.models.data_models import AnalysisOutput, ExplanationOutput, ExplanationBlock


class ExplainService:
    """
    Service class for handling data explanation v0.
    
    This service defines the contract for converting analysis results
    into user-facing explanations using template-based mapping.
    """
    
    def __init__(self, templates_path: Optional[str] = None):
        """
        Initialize the explanation service.
        
        Args:
            templates_path: Optional path to explanation templates JSON file. If not provided, uses default.
        """
        if templates_path is None:
            # Default to explanation_templates_v0.json in the copy directory
            current_dir = Path(__file__).parent
            templates_path = str(current_dir / "copy" / "explanation_templates_v0.json")
        
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
            if 'overall_messages' not in self.templates:
                raise ValueError("Templates file must contain 'overall_messages'")
            
            if 'risk_explanations' not in self.templates:
                raise ValueError("Templates file must contain 'risk_explanations'")
            
            # Validate overall_messages has low, medium, high
            overall_messages = self.templates['overall_messages']
            for level in ['low', 'medium', 'high']:
                if level not in overall_messages:
                    raise ValueError(f"overall_messages must contain '{level}'")
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in templates file: {e}")
    
    def explain(self, analysis_output: AnalysisOutput) -> ExplanationOutput:
        """
        Convert AnalysisOutput into user-facing ExplanationOutput.

        This method:
        1. Uses neutral overall message (no risk level-based judgment)
        2. Maps each risk_item to an explanation_block using templates
        3. Gracefully skips risk_items with unknown risk_codes
        4. Does not use any conclusion-type information (severity, risk_level)

        Args:
            analysis_output: AnalysisOutput from the analysis layer

        Returns:
            ExplanationOutput containing overall_message and explanation_blocks
        """
        # Use neutral overall message (no risk level-based judgment)
        overall_message = "我们发现了一些需要您注意的条款。请查看以下详细信息。"
        
        # Map each risk_item to an explanation_block
        explanation_blocks: List[ExplanationBlock] = []
        risk_explanations = self.templates.get('risk_explanations', {})
        
        for risk_item in analysis_output.risk_items:
            risk_code = risk_item.risk_code
            
            # Check if template exists for this risk_code
            if risk_code not in risk_explanations:
                # Gracefully skip unknown risk_codes
                continue
            
            template = risk_explanations[risk_code]
            
            # Create explanation block with minimal information
            explanation_block = ExplanationBlock(
                title=template['title'],
                message=template['message'],
                user_action=template['user_action'],
                severity='low',  # Default value, not intended for user-facing
                risk_code=risk_code
            )
            
            explanation_blocks.append(explanation_block)
        
        return ExplanationOutput(
            overall_message=overall_message,
            explanation_blocks=explanation_blocks
        )

