"""
Explanation Service v1 (PAID)
=============================
This service handles the explanation layer responsibilities for PAID tier:
- Providing structured Next-Step Risk Guide
- Offering clear action paths for different user intentions

IMPORTANT: explain v1 = PAID tier
- Provides structured next-step guidance
- Includes three-section output format
- No model enhancements or new analysis capabilities

Why can't merge with v0:
- v0 is FREE tier with minimal functionality
- v1 is PAID tier with premium guidance
- Business model requires clear separation between free and paid features
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from backend.models.data_models import RiskField, RiskFieldExplanation, ExplanationOutputV1


class ExplainV1Service:
    """
    Service class for handling structural risk field explanations v1 (PAID).
    
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
        # Note: Template loading will be implemented in future iterations
    
    def explain(self, risk_fields: List[RiskField]) -> ExplanationOutputV1:
        """
        Convert risk_fields into structural risk explanations.
        
        Args:
            risk_fields: List of RiskField objects from analysis layer
            
        Returns:
            ExplanationOutputV1 containing list of risk_field_explanations
        """
        # Note: Implementation will be completed in future iterations
        # For now, return empty list as placeholder
        return ExplanationOutputV1(risk_field_explanations=[])
    
    def get_next_step_risk_guide(self, risk_fields: List[RiskField]) -> Dict[str, Any]:
        """
        Generate Next-Step Risk Guide for PAID tier.
        
        Structured output (three-section format):
        - If you continue: What happens if user proceeds
        - If you want to negotiate: What to negotiate
        - If you pause: Options for pausing
        
        Args:
            risk_fields: List of RiskField objects from analysis layer
            
        Returns:
            Structured Next-Step Risk Guide
        """
        # Only implementing structure, not content
        return {
            "if_you_continue": {
                "title": "If you continue",
                "content": "Placeholder: What happens if you proceed with the current terms"
            },
            "if_you_want_to_negotiate": {
                "title": "If you want to negotiate",
                "content": "Placeholder: What terms you might want to negotiate"
            },
            "if_you_pause": {
                "title": "If you pause",
                "content": "Placeholder: Options for pausing and seeking more information"
            }
        }
