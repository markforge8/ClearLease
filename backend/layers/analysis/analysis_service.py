"""
Analysis Service
===============
This service handles the analysis layer responsibilities:
- Loading analysis rules that map rule_id to risk_code
- Aggregating evidence per risk_code
- Setting severity per risk_code
- Calculating overall risk_level

This service implements the analysis v0 contract with rule-based risk aggregation.
No AI, interpretation, LLM, or additional logic is used.
"""

import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from collections import defaultdict
from models.data_models import (
    AnalysisInput,
    AnalysisOutput,
    AnalysisSummary,
    RiskItem,
    ExtractedSignal
)
from layers.analysis.risk_builder_v1 import RiskBuilderV1


class AnalysisService:
    """
    Service class for handling data analysis v0.
    
    This service defines the contract for analyzing extracted signals
    and converting them into risk judgments using rule-based aggregation.
    """
    
    def __init__(self, rules_path: Optional[str] = None):
        """
        Initialize the analysis service.
        
        Args:
            rules_path: Optional path to analysis rules JSON file. If not provided, uses default.
        """
        if rules_path is None:
            # Default to analysis_rules_v0.json in the same directory
            current_dir = Path(__file__).parent
            rules_path = str(current_dir / "rules" / "analysis_rules_v0.json")
        
        self.rules_path = rules_path
        self.risk_mappings: Dict[str, Dict[str, Any]] = {}
        self._load_rules()
    
    def _load_rules(self) -> None:
        """
        Load analysis rules from JSON file.
        Maps rule_id to risk_code with severity.
        
        Raises:
            FileNotFoundError: If rules file does not exist
            ValueError: If rules file is invalid
        """
        if not os.path.exists(self.rules_path):
            raise FileNotFoundError(f"Analysis rules file not found: {self.rules_path}")
        
        try:
            with open(self.rules_path, 'r', encoding='utf-8') as f:
                rules_data = json.load(f)
            
            if 'risk_mappings' not in rules_data:
                raise ValueError("Rules file must contain 'risk_mappings' array")
            
            # Build mapping from rule_id to risk information
            for mapping in rules_data['risk_mappings']:
                if 'rule_id' not in mapping or 'risk_code' not in mapping or 'severity' not in mapping:
                    raise ValueError("Each risk_mapping must have 'rule_id', 'risk_code', and 'severity'")
                
                rule_id = mapping['rule_id']
                self.risk_mappings[rule_id] = {
                    'risk_code': mapping['risk_code'],
                    'severity': mapping['severity'],
                    'description': mapping.get('description', '')
                }
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in rules file: {e}")
    
    def analyze(self, input_data: AnalysisInput) -> AnalysisOutput:
        """
        Analyze extracted signals and convert them into risk judgments.
        
        This method:
        1. Maps rule_id → risk_code using loaded rules
        2. Aggregates evidence per risk_code
        3. Sets severity per risk_code
        4. Calculates overall risk_level
        
        Args:
            input_data: AnalysisInput containing doc_id and extracted_signals
            
        Returns:
            AnalysisOutput containing analysis_summary and risk_items
        """
        # Aggregate evidence per risk_code
        risk_evidence: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'rule_ids': [],
            'severity': None,
            'description': ''
        })
        
        # Map rule_id → risk_code and aggregate
        for signal in input_data.extracted_signals:
            rule_id = signal.rule_id
            
            if rule_id in self.risk_mappings:
                mapping = self.risk_mappings[rule_id]
                risk_code = mapping['risk_code']
                severity = mapping['severity']
                description = mapping['description']
                
                # Aggregate evidence
                risk_evidence[risk_code]['rule_ids'].append(rule_id)
                risk_evidence[risk_code]['severity'] = severity
                risk_evidence[risk_code]['description'] = description
        
        # Build risk_items
        risk_items = []
        risk_flags = []
        severities = []
        
        for risk_code, evidence in risk_evidence.items():
            if evidence['rule_ids']:  # Only include if there's evidence
                risk_item = RiskItem(
                    risk_code=risk_code,
                    severity=evidence['severity'],
                    evidence_rules=evidence['rule_ids'],
                    description=evidence['description']
                )
                risk_items.append(risk_item)
                risk_flags.append(risk_code)
                severities.append(evidence['severity'])
        
        # Calculate overall risk_level
        risk_level = self._calculate_overall_risk_level(severities)
        
        # Build analysis_summary
        analysis_summary = AnalysisSummary(
            risk_level=risk_level,
            risk_flags=risk_flags,
            confidence=1.0  # Rule-based, so confidence is always 1.0
        )
        
        # Build v1 risk_fields using RiskBuilderV1
        # Create temporary AnalysisOutput for RiskBuilderV1.build()
        temp_output = AnalysisOutput(
            analysis_summary=analysis_summary,
            risk_items=risk_items
        )
        risk_builder = RiskBuilderV1()
        risk_fields = risk_builder.build(temp_output, input_data.extracted_signals)
        
        # Return AnalysisOutput with risk_fields (defaults to [] if no structural risks)
        return AnalysisOutput(
            analysis_summary=analysis_summary,
            risk_items=risk_items,
            risk_fields=risk_fields
        )
    
    def _calculate_overall_risk_level(self, severities: List[str]) -> str:
        """
        Calculate overall risk level based on severities.
        
        Logic:
        - high if any risk severity is high
        - medium if none high but at least one medium
        - low otherwise
        
        Args:
            severities: List of severity strings (low, medium, high)
            
        Returns:
            Overall risk level string (low, medium, high)
        """
        if not severities:
            return "low"
        
        if "high" in severities:
            return "high"
        elif "medium" in severities:
            return "medium"
        else:
            return "low"

