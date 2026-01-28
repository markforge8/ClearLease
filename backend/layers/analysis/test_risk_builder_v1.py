"""
Unit tests for RiskBuilderV1.
Tests structural risk field generation from v0 analysis output.
"""

import unittest
from pathlib import Path
from backend.layers.analysis.risk_builder_v1 import RiskBuilderV1
from backend.models.data_models import (
    AnalysisOutput,
    AnalysisSummary,
    RiskItem,
    ExtractedSignal,
    RiskAxis
)


class TestRiskBuilderV1(unittest.TestCase):
    """
    Unit tests for RiskBuilderV1.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.builder = RiskBuilderV1()
    
    def test_build_with_no_risks(self):
        """Test build with no risk items - should return empty list."""
        analysis_output = AnalysisOutput(
            analysis_summary=AnalysisSummary(
                risk_level="low",
                risk_flags=[],
                confidence=1.0
            ),
            risk_items=[]
        )
        extracted_signals = []
        
        risk_fields = self.builder.build(analysis_output, extracted_signals)
        
        # Assertions
        self.assertEqual(len(risk_fields), 0)
        self.assertEqual(risk_fields, [])
    
    def test_build_with_single_responsibility_risk(self):
        """Test build with single responsibility transfer risk."""
        analysis_output = AnalysisOutput(
            analysis_summary=AnalysisSummary(
                risk_level="medium",
                risk_flags=["LIABILITY_LIMITATION"],
                confidence=1.0
            ),
            risk_items=[
                RiskItem(
                    risk_code="LIABILITY_LIMITATION",
                    severity="medium",
                    evidence_rules=["keyword_007"],
                    description="Limitation or exclusion of liability detected"
                )
            ]
        )
        extracted_signals = [
            ExtractedSignal(
                rule_id="keyword_007",
                type="keyword",
                hit_text="liability",
                block_id="block_0",
                order=0
            )
        ]
        
        risk_fields = self.builder.build(analysis_output, extracted_signals)
        
        # Assertions - should have one responsibility risk field
        self.assertEqual(len(risk_fields), 1)
        self.assertEqual(risk_fields[0].axis, RiskAxis.RESPONSIBILITY)
        self.assertEqual(risk_fields[0].affected_party, "tenant")
        self.assertEqual(risk_fields[0].intensity, "high")
        self.assertEqual(risk_fields[0].compounding, True)
        self.assertIn("block_0", risk_fields[0].source_blocks)
        self.assertIsInstance(risk_fields[0].description, str)
        self.assertGreater(len(risk_fields[0].description), 0)
    
    def test_build_with_single_temporal_risk(self):
        """Test build with single temporal risk (AUTO_RENEWAL)."""
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
        extracted_signals = [
            ExtractedSignal(
                rule_id="keyword_001",
                type="keyword",
                hit_text="lease",
                block_id="block_1",
                order=0
            )
        ]
        
        risk_fields = self.builder.build(analysis_output, extracted_signals)
        
        # Assertions - should have one temporal risk field
        self.assertEqual(len(risk_fields), 1)
        self.assertEqual(risk_fields[0].axis, RiskAxis.TEMPORAL)
        self.assertEqual(risk_fields[0].affected_party, "tenant")
        self.assertEqual(risk_fields[0].intensity, "medium")
        self.assertEqual(risk_fields[0].compounding, False)
        self.assertIn("block_1", risk_fields[0].source_blocks)
        self.assertIsInstance(risk_fields[0].description, str)
        self.assertGreater(len(risk_fields[0].description), 0)
    
    def test_build_with_multiple_risks(self):
        """Test build with multiple risk types - should return multiple risk fields."""
        analysis_output = AnalysisOutput(
            analysis_summary=AnalysisSummary(
                risk_level="high",
                risk_flags=["AUTO_RENEWAL", "LIABILITY_LIMITATION"],
                confidence=1.0
            ),
            risk_items=[
                RiskItem(
                    risk_code="AUTO_RENEWAL",
                    severity="medium",
                    evidence_rules=["phrase_001"],
                    description="Automatic renewal phrases detected"
                ),
                RiskItem(
                    risk_code="LIABILITY_LIMITATION",
                    severity="medium",
                    evidence_rules=["phrase_012"],
                    description="Liability limitation clauses detected"
                )
            ]
        )
        extracted_signals = [
            ExtractedSignal(
                rule_id="phrase_001",
                type="phrase",
                hit_text="lease agreement",
                block_id="block_0",
                order=0
            ),
            ExtractedSignal(
                rule_id="phrase_012",
                type="phrase",
                hit_text="liability limitation",
                block_id="block_1",
                order=1
            )
        ]
        
        risk_fields = self.builder.build(analysis_output, extracted_signals)
        
        # Assertions - should have multiple risk fields
        self.assertGreaterEqual(len(risk_fields), 1)
        
        # Check that we have both temporal and responsibility risks
        axes = [rf.axis for rf in risk_fields]
        self.assertIn(RiskAxis.TEMPORAL, axes)
        self.assertIn(RiskAxis.RESPONSIBILITY, axes)
        
        # Check structure of each risk field
        for rf in risk_fields:
            self.assertIn(rf.axis, [RiskAxis.TEMPORAL, RiskAxis.RESPONSIBILITY])
            self.assertIn(rf.affected_party, ["tenant", "landlord"])
            self.assertIn(rf.intensity, ["low", "medium", "high"])
            self.assertIsInstance(rf.compounding, bool)
            self.assertIsInstance(rf.description, str)
            self.assertGreater(len(rf.description), 0)
            self.assertIsInstance(rf.source_blocks, list)
            self.assertGreater(len(rf.source_blocks), 0)
        
        # Check source_blocks contain the expected block_ids
        all_source_blocks = []
        for rf in risk_fields:
            all_source_blocks.extend(rf.source_blocks)
        self.assertIn("block_0", all_source_blocks)
        self.assertIn("block_1", all_source_blocks)
    
    def test_build_with_unknown_risk_code(self):
        """Test build with risk codes that don't trigger v1 risk fields."""
        analysis_output = AnalysisOutput(
            analysis_summary=AnalysisSummary(
                risk_level="high",
                risk_flags=["UNILATERAL_CHANGE"],
                confidence=1.0
            ),
            risk_items=[
                RiskItem(
                    risk_code="UNILATERAL_CHANGE",
                    severity="high",
                    evidence_rules=["structural_002"],
                    description="One party may change contract terms unilaterally"
                )
            ]
        )
        extracted_signals = [
            ExtractedSignal(
                rule_id="structural_002",
                type="structural",
                hit_text="$1000",
                block_id="block_2",
                order=0
            )
        ]
        
        risk_fields = self.builder.build(analysis_output, extracted_signals)
        
        # Assertions - UNILATERAL_CHANGE doesn't trigger our current rules
        # So risk_fields should be empty
        self.assertEqual(len(risk_fields), 0)
        self.assertEqual(risk_fields, [])


if __name__ == '__main__':
    unittest.main()

