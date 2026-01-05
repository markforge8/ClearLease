"""
Unit tests for AnalysisService v0.
Tests rule-based risk aggregation with mocked extracted_signals.
"""

import unittest
from pathlib import Path
from backend.layers.analysis.analysis_service import AnalysisService
from backend.models.data_models import AnalysisInput, ExtractedSignal


class TestAnalysisService(unittest.TestCase):
    """
    Unit tests for AnalysisService v0.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        # Use the default rules path
        current_dir = Path(__file__).parent
        rules_path = str(current_dir / "rules" / "analysis_rules_v0.json")
        self.service = AnalysisService(rules_path=rules_path)
    
    def test_analyze_with_single_medium_risk_signal(self):
        """Test analysis with a single medium-risk signal."""
        input_data = AnalysisInput(
            doc_id="test_doc_001",
            extracted_signals=[
                ExtractedSignal(
                    rule_id="phrase_001",
                    type="phrase",
                    hit_text="automatic renewal",
                    block_id="block_0",
                    order=0
                )
            ]
        )
        
        result = self.service.analyze(input_data)
        
        # Assertions
        self.assertEqual(result.analysis_summary.risk_level, "medium")
        self.assertEqual(len(result.risk_items), 1)
        self.assertEqual(result.risk_items[0].risk_code, "AUTO_RENEWAL")
        self.assertEqual(result.risk_items[0].severity, "medium")
        self.assertIn("phrase_001", result.risk_items[0].evidence_rules)
        self.assertEqual(result.analysis_summary.confidence, 1.0)
    
    def test_analyze_with_medium_risk_signal(self):
        """Test analysis with a medium-risk signal."""
        input_data = AnalysisInput(
            doc_id="test_doc_002",
            extracted_signals=[
                ExtractedSignal(
                    rule_id="keyword_001",
                    type="keyword",
                    hit_text="lease",
                    block_id="block_0",
                    order=0
                )
            ]
        )
        
        result = self.service.analyze(input_data)
        
        # Assertions
        self.assertEqual(result.analysis_summary.risk_level, "medium")
        self.assertEqual(len(result.risk_items), 1)
        self.assertEqual(result.risk_items[0].risk_code, "AUTO_RENEWAL")
        self.assertEqual(result.risk_items[0].severity, "medium")
    
    def test_analyze_with_multiple_signals_same_risk(self):
        """Test analysis with multiple signals mapping to the same risk_code."""
        input_data = AnalysisInput(
            doc_id="test_doc_003",
            extracted_signals=[
                ExtractedSignal(
                    rule_id="keyword_001",
                    type="keyword",
                    hit_text="lease",
                    block_id="block_0",
                    order=0
                ),
                ExtractedSignal(
                    rule_id="keyword_001",
                    type="keyword",
                    hit_text="tenant",
                    block_id="block_0",
                    order=1
                )
            ]
        )
        
        result = self.service.analyze(input_data)
        
        # Assertions
        self.assertEqual(result.analysis_summary.risk_level, "medium")
        self.assertEqual(len(result.risk_items), 1)
        self.assertEqual(len(result.risk_items[0].evidence_rules), 2)
        self.assertIn("keyword_001", result.risk_items[0].evidence_rules)
    
    def test_analyze_with_multiple_different_risks(self):
        """Test analysis with signals mapping to different risk codes."""
        input_data = AnalysisInput(
            doc_id="test_doc_004",
            extracted_signals=[
                ExtractedSignal(
                    rule_id="phrase_001",
                    type="phrase",
                    hit_text="automatic renewal",
                    block_id="block_0",
                    order=0
                ),
                ExtractedSignal(
                    rule_id="structural_002",
                    type="structural",
                    hit_text="unilateral change",
                    block_id="block_0",
                    order=1
                )
            ]
        )
        
        result = self.service.analyze(input_data)
        
        # Assertions - structural_002 is high severity, so overall should be high
        self.assertEqual(result.analysis_summary.risk_level, "high")
        self.assertEqual(len(result.risk_items), 2)
        risk_codes = [item.risk_code for item in result.risk_items]
        self.assertIn("AUTO_RENEWAL", risk_codes)
        self.assertIn("UNILATERAL_CHANGE", risk_codes)
        self.assertEqual(len(result.analysis_summary.risk_flags), 2)
    
    def test_analyze_with_unknown_rule_id(self):
        """Test analysis with a signal that has an unknown rule_id."""
        input_data = AnalysisInput(
            doc_id="test_doc_005",
            extracted_signals=[
                ExtractedSignal(
                    rule_id="unknown_rule",
                    type="keyword",
                    hit_text="unknown",
                    block_id="block_0",
                    order=0
                )
            ]
        )
        
        result = self.service.analyze(input_data)
        
        # Assertions - unknown rules should be ignored
        self.assertEqual(result.analysis_summary.risk_level, "low")
        self.assertEqual(len(result.risk_items), 0)
        self.assertEqual(len(result.analysis_summary.risk_flags), 0)
    
    def test_analyze_with_no_signals(self):
        """Test analysis with no extracted signals."""
        input_data = AnalysisInput(
            doc_id="test_doc_006",
            extracted_signals=[]
        )
        
        result = self.service.analyze(input_data)
        
        # Assertions
        self.assertEqual(result.analysis_summary.risk_level, "low")
        self.assertEqual(len(result.risk_items), 0)
        self.assertEqual(len(result.analysis_summary.risk_flags), 0)
    
    def test_risk_level_calculation_high(self):
        """Test that overall risk level is high when any severity is high."""
        input_data = AnalysisInput(
            doc_id="test_doc_007",
            extracted_signals=[
                ExtractedSignal(
                    rule_id="phrase_003",
                    type="phrase",
                    hit_text="limited notice",
                    block_id="block_0",
                    order=0
                )
            ]
        )
        
        result = self.service.analyze(input_data)
        
        # phrase_003 maps to LIMITED_NOTICE with high severity
        self.assertEqual(result.analysis_summary.risk_level, "high")
        self.assertEqual(len(result.risk_items), 1)
        self.assertEqual(result.risk_items[0].risk_code, "LIMITED_NOTICE")
        self.assertEqual(result.risk_items[0].severity, "high")


if __name__ == '__main__':
    unittest.main()

