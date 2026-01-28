"""
Unit tests for ExplainV1Service.
Tests structural risk field explanation generation from risk_fields.
"""

import unittest
from pathlib import Path
from backend.layers.explain.explain_v1_service import ExplainV1Service
from backend.models.data_models import (
    RiskField,
    RiskAxis,
    ExplanationOutputV1
)


class TestExplainV1Service(unittest.TestCase):
    """
    Unit tests for ExplainV1Service.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        # Use the default templates path
        current_dir = Path(__file__).parent
        templates_path = str(current_dir / "copy" / "explanation_templates_v1.json")
        self.service = ExplainV1Service(templates_path=templates_path)
    
    def test_explain_with_empty_risk_fields(self):
        """Test explanation with empty risk_fields - should return empty list."""
        risk_fields = []
        
        result = self.service.explain(risk_fields)
        
        # Assertions
        self.assertIsInstance(result, ExplanationOutputV1)
        self.assertEqual(len(result.risk_field_explanations), 0)
        self.assertEqual(result.risk_field_explanations, [])
    
    def test_explain_with_single_temporal_risk_field(self):
        """Test explanation with single temporal risk field."""
        risk_fields = [
            RiskField(
                axis=RiskAxis.TEMPORAL,
                affected_party="tenant",
                intensity="medium",
                compounding=False,
                description="合同包含自动续约条款。",
                source_blocks=["block_0", "block_1"]
            )
        ]
        
        result = self.service.explain(risk_fields)
        
        # Assertions
        self.assertIsInstance(result, ExplanationOutputV1)
        self.assertEqual(len(result.risk_field_explanations), 1)
        
        explanation = result.risk_field_explanations[0]
        self.assertEqual(explanation.axis, RiskAxis.TEMPORAL)
        self.assertEqual(explanation.intensity, "medium")
        self.assertEqual(explanation.affected_party, "tenant")
        self.assertEqual(explanation.compounding, False)
        self.assertEqual(explanation.source_blocks, ["block_0", "block_1"])
        self.assertIsInstance(explanation.title, str)
        self.assertGreater(len(explanation.title), 0)
        self.assertIsInstance(explanation.message, str)
        self.assertGreater(len(explanation.message), 0)
        self.assertIsInstance(explanation.user_action, str)
        self.assertGreater(len(explanation.user_action), 0)
    
    def test_explain_with_single_responsibility_risk_field(self):
        """Test explanation with single responsibility risk field."""
        risk_fields = [
            RiskField(
                axis=RiskAxis.RESPONSIBILITY,
                affected_party="tenant",
                intensity="high",
                compounding=True,
                description="房东将维护责任转嫁给租客。",
                source_blocks=["block_2"]
            )
        ]
        
        result = self.service.explain(risk_fields)
        
        # Assertions
        self.assertIsInstance(result, ExplanationOutputV1)
        self.assertEqual(len(result.risk_field_explanations), 1)
        
        explanation = result.risk_field_explanations[0]
        self.assertEqual(explanation.axis, RiskAxis.RESPONSIBILITY)
        self.assertEqual(explanation.intensity, "high")
        self.assertEqual(explanation.affected_party, "tenant")
        self.assertEqual(explanation.compounding, True)
        self.assertEqual(explanation.source_blocks, ["block_2"])
        self.assertIsInstance(explanation.title, str)
        self.assertIsInstance(explanation.message, str)
        self.assertIsInstance(explanation.user_action, str)
    
    def test_explain_with_single_liability_risk_field(self):
        """Test explanation with single liability risk field."""
        risk_fields = [
            RiskField(
                axis=RiskAxis.LIABILITY,
                affected_party="tenant",
                intensity="low",
                compounding=False,
                description="合同中存在责任限制条款。",
                source_blocks=["block_3"]
            )
        ]
        
        result = self.service.explain(risk_fields)
        
        # Assertions
        self.assertIsInstance(result, ExplanationOutputV1)
        self.assertEqual(len(result.risk_field_explanations), 1)
        
        explanation = result.risk_field_explanations[0]
        self.assertEqual(explanation.axis, RiskAxis.LIABILITY)
        self.assertEqual(explanation.intensity, "low")
        self.assertEqual(explanation.affected_party, "tenant")
    
    def test_explain_with_multiple_risk_fields(self):
        """Test explanation with multiple risk fields of different axes and intensities."""
        risk_fields = [
            RiskField(
                axis=RiskAxis.TEMPORAL,
                affected_party="tenant",
                intensity="medium",
                compounding=False,
                description="合同包含自动续约条款。",
                source_blocks=["block_0"]
            ),
            RiskField(
                axis=RiskAxis.RESPONSIBILITY,
                affected_party="tenant",
                intensity="high",
                compounding=True,
                description="房东将维护责任转嫁给租客。",
                source_blocks=["block_1", "block_2"]
            ),
            RiskField(
                axis=RiskAxis.LIABILITY,
                affected_party="tenant",
                intensity="medium",
                compounding=False,
                description="合同中存在责任限制条款。",
                source_blocks=["block_3"]
            )
        ]
        
        result = self.service.explain(risk_fields)
        
        # Assertions
        self.assertIsInstance(result, ExplanationOutputV1)
        self.assertEqual(len(result.risk_field_explanations), 3)
        
        # Check that all axes are present
        axes = [exp.axis for exp in result.risk_field_explanations]
        self.assertIn(RiskAxis.TEMPORAL, axes)
        self.assertIn(RiskAxis.RESPONSIBILITY, axes)
        self.assertIn(RiskAxis.LIABILITY, axes)
        
        # Check structure of each explanation
        for explanation in result.risk_field_explanations:
            self.assertIn(explanation.axis, [RiskAxis.TEMPORAL, RiskAxis.RESPONSIBILITY, RiskAxis.LIABILITY])
            self.assertIn(explanation.intensity, ["low", "medium", "high"])
            self.assertIn(explanation.affected_party, ["tenant", "landlord"])
            self.assertIsInstance(explanation.compounding, bool)
            self.assertIsInstance(explanation.title, str)
            self.assertGreater(len(explanation.title), 0)
            self.assertIsInstance(explanation.message, str)
            self.assertGreater(len(explanation.message), 0)
            self.assertIsInstance(explanation.user_action, str)
            self.assertGreater(len(explanation.user_action), 0)
            self.assertIsInstance(explanation.source_blocks, list)
            self.assertGreater(len(explanation.source_blocks), 0)
    
    def test_explain_with_different_intensities(self):
        """Test explanation with different intensity levels."""
        risk_fields = [
            RiskField(
                axis=RiskAxis.TEMPORAL,
                affected_party="tenant",
                intensity="low",
                compounding=False,
                description="低强度时间风险",
                source_blocks=["block_0"]
            ),
            RiskField(
                axis=RiskAxis.TEMPORAL,
                affected_party="tenant",
                intensity="high",
                compounding=True,
                description="高强度时间风险",
                source_blocks=["block_1"]
            )
        ]
        
        result = self.service.explain(risk_fields)
        
        # Assertions
        self.assertIsInstance(result, ExplanationOutputV1)
        self.assertEqual(len(result.risk_field_explanations), 2)
        
        # Check that different intensities produce different explanations
        intensities = [exp.intensity for exp in result.risk_field_explanations]
        self.assertIn("low", intensities)
        self.assertIn("high", intensities)
        
        # Verify that titles/messages differ for different intensities
        low_exp = next(exp for exp in result.risk_field_explanations if exp.intensity == "low")
        high_exp = next(exp for exp in result.risk_field_explanations if exp.intensity == "high")
        self.assertNotEqual(low_exp.title, high_exp.title)
        self.assertNotEqual(low_exp.message, high_exp.message)


if __name__ == '__main__':
    unittest.main()

