"""
Unit tests for ExplainService v0.
Tests template-based explanation generation with mocked AnalysisOutput.
"""

import unittest
from pathlib import Path
from backend.layers.explain.explain_service import ExplainService
from backend.models.data_models import (
    AnalysisOutput,
    AnalysisSummary,
    RiskItem,
    ExplanationOutput
)


class TestExplainService(unittest.TestCase):
    """
    Unit tests for ExplainService v0.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        # Use the default templates path
        current_dir = Path(__file__).parent
        templates_path = str(current_dir / "copy" / "explanation_templates_v0.json")
        self.service = ExplainService(templates_path=templates_path)
    
    def test_explain_with_low_risk_level(self):
        """Test explanation with low risk level."""
        analysis_output = AnalysisOutput(
            analysis_summary=AnalysisSummary(
                risk_level="low",
                risk_flags=[],
                confidence=1.0
            ),
            risk_items=[]
        )
        
        result = self.service.explain(analysis_output)
        
        # Assertions
        self.assertIsInstance(result, ExplanationOutput)
        self.assertEqual(result.overall_message, "No major risk indicators were detected in this contract.")
        self.assertEqual(len(result.explanation_blocks), 0)
    
    def test_explain_with_medium_risk_level(self):
        """Test explanation with medium risk level."""
        analysis_output = AnalysisOutput(
            analysis_summary=AnalysisSummary(
                risk_level="medium",
                risk_flags=["AUTO_RENEWAL"],
                confidence=1.0
            ),
            risk_items=[
                RiskItem(
                    risk_code="AUTO_RENEWAL",
                    severity="medium",
                    evidence_rules=["keyword_001"],
                    description="Automatic renewal related terms detected"
                )
            ]
        )
        
        result = self.service.explain(analysis_output)
        
        # Assertions
        self.assertIsInstance(result, ExplanationOutput)
        self.assertEqual(result.overall_message, "Some contract terms may require your attention.")
        self.assertEqual(len(result.explanation_blocks), 1)
        self.assertEqual(result.explanation_blocks[0].title, "Automatic Renewal")
        self.assertEqual(result.explanation_blocks[0].severity, "medium")
        self.assertEqual(result.explanation_blocks[0].risk_code, "AUTO_RENEWAL")
        self.assertIn("renew automatically", result.explanation_blocks[0].message.lower())
        self.assertIsNotNone(result.explanation_blocks[0].user_action)
    
    def test_explain_with_high_risk_level(self):
        """Test explanation with high risk level."""
        analysis_output = AnalysisOutput(
            analysis_summary=AnalysisSummary(
                risk_level="high",
                risk_flags=["LIMITED_NOTICE"],
                confidence=1.0
            ),
            risk_items=[
                RiskItem(
                    risk_code="LIMITED_NOTICE",
                    severity="high",
                    evidence_rules=["phrase_003"],
                    description="Contract changes or renewal without sufficient prior notice"
                )
            ]
        )
        
        result = self.service.explain(analysis_output)
        
        # Assertions
        self.assertIsInstance(result, ExplanationOutput)
        self.assertEqual(result.overall_message, "This contract contains terms that should be reviewed carefully.")
        self.assertEqual(len(result.explanation_blocks), 1)
        self.assertEqual(result.explanation_blocks[0].title, "Limited Prior Notice")
        self.assertEqual(result.explanation_blocks[0].severity, "high")
        self.assertEqual(result.explanation_blocks[0].risk_code, "LIMITED_NOTICE")
    
    def test_explain_with_multiple_risk_items(self):
        """Test explanation with multiple risk items."""
        analysis_output = AnalysisOutput(
            analysis_summary=AnalysisSummary(
                risk_level="high",
                risk_flags=["AUTO_RENEWAL", "UNILATERAL_CHANGE"],
                confidence=1.0
            ),
            risk_items=[
                RiskItem(
                    risk_code="AUTO_RENEWAL",
                    severity="medium",
                    evidence_rules=["keyword_001"],
                    description="Automatic renewal related terms detected"
                ),
                RiskItem(
                    risk_code="UNILATERAL_CHANGE",
                    severity="high",
                    evidence_rules=["phrase_006"],
                    description="One party may change contract terms unilaterally"
                )
            ]
        )
        
        result = self.service.explain(analysis_output)
        
        # Assertions
        self.assertIsInstance(result, ExplanationOutput)
        self.assertEqual(result.overall_message, "This contract contains terms that should be reviewed carefully.")
        self.assertEqual(len(result.explanation_blocks), 2)
        
        risk_codes = [block.risk_code for block in result.explanation_blocks]
        self.assertIn("AUTO_RENEWAL", risk_codes)
        self.assertIn("UNILATERAL_CHANGE", risk_codes)
        
        # Verify each block has required fields
        for block in result.explanation_blocks:
            self.assertIsNotNone(block.title)
            self.assertIsNotNone(block.message)
            self.assertIsNotNone(block.user_action)
            self.assertIn(block.severity, ["low", "medium", "high"])
            self.assertIsNotNone(block.risk_code)
    
    def test_explain_with_unknown_risk_code(self):
        """Test explanation with unknown risk_code (should gracefully skip)."""
        analysis_output = AnalysisOutput(
            analysis_summary=AnalysisSummary(
                risk_level="medium",
                risk_flags=["UNKNOWN_RISK"],
                confidence=1.0
            ),
            risk_items=[
                RiskItem(
                    risk_code="UNKNOWN_RISK",
                    severity="medium",
                    evidence_rules=["unknown_rule"],
                    description="Unknown risk"
                )
            ]
        )
        
        result = self.service.explain(analysis_output)
        
        # Assertions - unknown risk_code should be skipped
        self.assertIsInstance(result, ExplanationOutput)
        self.assertEqual(result.overall_message, "Some contract terms may require your attention.")
        self.assertEqual(len(result.explanation_blocks), 0)
    
    def test_explain_with_mixed_known_and_unknown_risk_codes(self):
        """Test explanation with mix of known and unknown risk codes."""
        analysis_output = AnalysisOutput(
            analysis_summary=AnalysisSummary(
                risk_level="high",
                risk_flags=["AUTO_RENEWAL", "UNKNOWN_RISK"],
                confidence=1.0
            ),
            risk_items=[
                RiskItem(
                    risk_code="AUTO_RENEWAL",
                    severity="medium",
                    evidence_rules=["keyword_001"],
                    description="Automatic renewal related terms detected"
                ),
                RiskItem(
                    risk_code="UNKNOWN_RISK",
                    severity="high",
                    evidence_rules=["unknown_rule"],
                    description="Unknown risk"
                )
            ]
        )
        
        result = self.service.explain(analysis_output)
        
        # Assertions - only known risk_code should be included
        self.assertIsInstance(result, ExplanationOutput)
        self.assertEqual(len(result.explanation_blocks), 1)
        self.assertEqual(result.explanation_blocks[0].risk_code, "AUTO_RENEWAL")
    
    def test_explain_all_risk_codes_from_templates(self):
        """Test that all risk codes in templates can be explained."""
        all_risk_codes = [
            "AUTO_RENEWAL",
            "LIMITED_NOTICE",
            "UNILATERAL_CHANGE",
            "EARLY_TERMINATION_PENALTY",
            "LIABILITY_LIMITATION",
            "DATA_SHARING"
        ]
        
        risk_items = [
            RiskItem(
                risk_code=risk_code,
                severity="medium",
                evidence_rules=[f"rule_{i}"],
                description=f"Test {risk_code}"
            )
            for i, risk_code in enumerate(all_risk_codes)
        ]
        
        analysis_output = AnalysisOutput(
            analysis_summary=AnalysisSummary(
                risk_level="high",
                risk_flags=all_risk_codes,
                confidence=1.0
            ),
            risk_items=risk_items
        )
        
        result = self.service.explain(analysis_output)
        
        # Assertions - all risk codes should have explanation blocks
        self.assertEqual(len(result.explanation_blocks), len(all_risk_codes))
        
        explained_risk_codes = [block.risk_code for block in result.explanation_blocks]
        for risk_code in all_risk_codes:
            self.assertIn(risk_code, explained_risk_codes)


if __name__ == '__main__':
    unittest.main()

