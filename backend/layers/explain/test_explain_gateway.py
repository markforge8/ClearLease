"""
Tests for Explain Gateway
==========================
These tests verify that Gateway does NOT:
- Infer missing fields
- Interpret explanation content
- Modify explanation fields
- Optimize or merge explanations

Gateway only:
- Aggregates outputs (pass-through)
- Encapsulates into GatewayOutput structure
- Preserves all fields as-is
"""

import unittest
from typing import Optional
from layers.explain.explain_gateway import ExplainGateway
from models.data_models import (
    ExplanationOutput,
    ExplanationOutputV1,
    ExplainV2Output,
    ExplanationBlock,
    RiskFieldExplanation,
    RiskAxis,
    TrapType,
    Strength,
    Beneficiary,
    Irreversibility,
    ConfidenceLevel,
    LockInDynamics,
    GatewayOutput
)


class TestExplainGateway(unittest.TestCase):
    """Tests for ExplainGateway - verify no inference or interpretation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.gateway = ExplainGateway()
    
    def test_gateway_aggregates_v0_only(self):
        """Test Gateway aggregates v0 output correctly (pass-through)."""
        v0_output = ExplanationOutput(
            overall_message="Test overall message",
            explanation_blocks=[
                ExplanationBlock(
                    title="Test Title",
                    message="Test Message",
                    user_action="Test Action",
                    severity="medium",
                    risk_code="TEST_CODE"
                )
            ]
        )
        
        result = self.gateway.aggregate(explain_v0_output=v0_output)
        
        # Verify structure is correct
        self.assertIsInstance(result, GatewayOutput)
        self.assertIn("v0", result.overview)
        self.assertEqual(len(result.key_findings), 1)
        self.assertEqual(len(result.next_actions), 1)
        self.assertIn("v0", result.details)
        
        # Verify pass-through (no modification)
        self.assertEqual(result.overview["v0"]["overall_message"], "Test overall message")
        self.assertEqual(result.key_findings[0]["title"], "Test Title")
        self.assertEqual(result.next_actions[0]["action"], "Test Action")
    
    def test_gateway_aggregates_v1_only(self):
        """Test Gateway aggregates v1 output correctly (pass-through)."""
        v1_output = ExplanationOutputV1(
            risk_field_explanations=[
                RiskFieldExplanation(
                    axis=RiskAxis.TEMPORAL,
                    intensity="high",
                    affected_party="tenant",
                    title="Test Title",
                    message="Test Message",
                    user_action="Test Action",
                    compounding=True,
                    source_blocks=["block_1", "block_2"]
                )
            ]
        )
        
        result = self.gateway.aggregate(explain_v1_output=v1_output)
        
        # Verify structure is correct
        self.assertIsInstance(result, GatewayOutput)
        self.assertIn("v1", result.overview)
        self.assertEqual(len(result.key_findings), 1)
        self.assertEqual(len(result.next_actions), 1)
        self.assertIn("v1", result.details)
        
        # Verify pass-through (no modification)
        self.assertEqual(result.key_findings[0]["title"], "Test Title")
        self.assertEqual(result.key_findings[0]["axis"], "temporal")
        self.assertEqual(result.next_actions[0]["action"], "Test Action")
    
    def test_gateway_aggregates_v2_as_black_box(self):
        """Test Gateway aggregates v2 output as black box (pass-through, no interpretation)."""
        v2_output = ExplainV2Output(
            mechanism=TrapType.TEMPORAL_LOCK_IN,
            headline="Test Headline",
            core_logic="Test Core Logic",
            power_map="Test Power Map",
            irreversibility=Irreversibility.PARTIALLY_REVERSIBLE,
            escape_window={"exists": True, "conditions": "Test conditions"},
            user_actions=["Action 1", "Action 2"],
            confidence_level=ConfidenceLevel.HIGH,
            lock_in_dynamics=LockInDynamics(description="Test lock-in dynamics")
        )
        
        result = self.gateway.aggregate(explain_v2_output=v2_output)
        
        # Verify structure is correct
        self.assertIsInstance(result, GatewayOutput)
        self.assertIn("v2", result.overview)
        self.assertEqual(len(result.key_findings), 1)
        self.assertEqual(len(result.next_actions), 2)
        self.assertIn("v2", result.details)
        
        # Verify pass-through (no modification, no interpretation)
        self.assertEqual(result.overview["v2"]["headline"], "Test Headline")
        self.assertEqual(result.key_findings[0]["core_logic"], "Test Core Logic")
        self.assertEqual(result.details["v2"]["escape_window"]["exists"], True)
        self.assertIn("lock_in_dynamics", result.details["v2"])
    
    def test_gateway_aggregates_all_versions(self):
        """Test Gateway aggregates v0, v1, v2 together."""
        v0_output = ExplanationOutput(
            overall_message="V0 Message",
            explanation_blocks=[]
        )
        v1_output = ExplanationOutputV1(
            risk_field_explanations=[]
        )
        v2_output = ExplainV2Output(
            mechanism=TrapType.ASYMMETRIC_POWER,
            headline="V2 Headline",
            core_logic="V2 Core Logic",
            power_map="V2 Power Map",
            irreversibility=Irreversibility.REVERSIBLE,
            escape_window={},
            user_actions=[],
            confidence_level=ConfidenceLevel.MEDIUM
        )
        
        result = self.gateway.aggregate(
            explain_v0_output=v0_output,
            explain_v1_output=v1_output,
            explain_v2_output=v2_output
        )
        
        # Verify all versions are present
        self.assertIn("v0", result.overview)
        self.assertIn("v1", result.overview)
        self.assertIn("v2", result.overview)
        self.assertIn("v0", result.details)
        self.assertIn("v1", result.details)
        self.assertIn("v2", result.details)
    
    def test_gateway_preserves_empty_fields(self):
        """Test Gateway preserves empty fields as-is (no inference)."""
        v2_output = ExplainV2Output(
            mechanism=TrapType.EXIT_BARRIER,
            headline="",  # Empty field
            core_logic="",
            power_map="",
            irreversibility=Irreversibility.IRREVERSIBLE,
            escape_window={},  # Empty dict
            user_actions=[],  # Empty list
            confidence_level=ConfidenceLevel.LOW
        )
        
        result = self.gateway.aggregate(explain_v2_output=v2_output)
        
        # Verify empty fields are preserved as-is (no inference or default values)
        self.assertEqual(result.overview["v2"]["headline"], "")
        self.assertEqual(result.key_findings[0]["core_logic"], "")
        self.assertEqual(result.details["v2"]["escape_window"], {})
        self.assertEqual(result.details["v2"]["user_actions"], [])
        # Gateway should NOT add default values or infer content
    
    def test_gateway_handles_missing_v2(self):
        """Test Gateway handles missing v2 output gracefully (no inference)."""
        v0_output = ExplanationOutput(
            overall_message="Test",
            explanation_blocks=[]
        )
        
        result = self.gateway.aggregate(explain_v0_output=v0_output)
        
        # Verify structure is stable even when v2 is missing
        self.assertIsInstance(result, GatewayOutput)
        self.assertIn("v0", result.overview)
        self.assertNotIn("v2", result.overview)
        self.assertIn("v0", result.details)
        self.assertNotIn("v2", result.details)
        # Gateway should NOT infer or create v2 fields when missing
    
    def test_gateway_structure_consistency(self):
        """Test Gateway output structure is always consistent regardless of content."""
        # Test with different v2 contents
        test_cases = [
            ExplainV2Output(
                mechanism=TrapType.TEMPORAL_LOCK_IN,
                headline="Case 1",
                core_logic="Logic 1",
                power_map="Map 1",
                irreversibility=Irreversibility.REVERSIBLE,
                escape_window={"test": 1},
                user_actions=["a"],
                confidence_level=ConfidenceLevel.HIGH,
                lock_in_dynamics=LockInDynamics(description="Dyn 1")
            ),
            ExplainV2Output(
                mechanism=TrapType.AMBIGUITY,
                headline="Case 2",
                core_logic="Logic 2",
                power_map="Map 2",
                irreversibility=Irreversibility.IRREVERSIBLE,
                escape_window={"test": 2},
                user_actions=["b", "c"],
                confidence_level=ConfidenceLevel.LOW
            )
        ]
        
        structures = []
        for v2_output in test_cases:
            result = self.gateway.aggregate(explain_v2_output=v2_output)
            structures.append({
                "overview_keys": set(result.overview.keys()),
                "details_keys": set(result.details.keys()),
                "has_key_findings": "key_findings" in result.__dict__,
                "has_next_actions": "next_actions" in result.__dict__
            })
        
        # Verify structure is identical regardless of content
        self.assertEqual(structures[0]["overview_keys"], structures[1]["overview_keys"])
        self.assertEqual(structures[0]["details_keys"], structures[1]["details_keys"])
        self.assertEqual(structures[0]["has_key_findings"], structures[1]["has_key_findings"])
        self.assertEqual(structures[0]["has_next_actions"], structures[1]["has_next_actions"])
    
    def test_gateway_does_not_modify_v2_fields(self):
        """Test Gateway does NOT modify v2 field values."""
        v2_output = ExplainV2Output(
            mechanism=TrapType.EXIT_BARRIER,
            headline="Original Headline",
            core_logic="Original Core Logic",
            power_map="Original Power Map",
            irreversibility=Irreversibility.PARTIALLY_REVERSIBLE,
            escape_window={"original": "value"},
            user_actions=["Original Action"],
            confidence_level=ConfidenceLevel.MEDIUM
        )
        
        result = self.gateway.aggregate(explain_v2_output=v2_output)
        
        # Verify all fields are preserved exactly as-is
        self.assertEqual(result.details["v2"]["headline"], "Original Headline")
        self.assertEqual(result.details["v2"]["core_logic"], "Original Core Logic")
        self.assertEqual(result.details["v2"]["power_map"], "Original Power Map")
        self.assertEqual(result.details["v2"]["escape_window"]["original"], "value")
        self.assertEqual(result.details["v2"]["user_actions"][0], "Original Action")
        # Gateway should NOT modify, transform, or optimize any fields


if __name__ == '__main__':
    unittest.main()


