"""
Unit tests for TrapEngineV2.
Tests temporal lock-in trap detection from risk signals.
"""

import unittest
from backend.layers.analysis.v2.trap_engine import TrapEngineV2
from backend.layers.analysis.v2.risk_chain_builder import RiskChainBuilder


class TestTrapEngineV2(unittest.TestCase):
    """
    Unit tests for TrapEngineV2.
    """
    
    def test_detect_trap_with_auto_renewal_only(self):
        """Test detection with AUTO_RENEWAL signal only - should detect trap with low severity."""
        risk_signals = [
            {
                "type": "AUTO_RENEWAL",
                "confidence": "medium",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        # Assertions
        self.assertEqual(len(traps), 1)
        self.assertEqual(traps[0].trap_type, "temporal_lock")
        self.assertEqual(traps[0].severity, "low")
        self.assertEqual(len(traps[0].related_signals), 1)
        self.assertEqual(traps[0].related_signals[0]["type"], "AUTO_RENEWAL")
    
    def test_detect_trap_with_multiple_signals(self):
        """Test detection with AUTO_RENEWAL + SHORT_NOTICE_WINDOW - should detect trap with high severity."""
        risk_signals = [
            {
                "type": "AUTO_RENEWAL",
                "confidence": "medium",
                "details": {}
            },
            {
                "type": "SHORT_NOTICE_WINDOW",
                "confidence": "high",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        # Assertions
        self.assertEqual(len(traps), 1)
        self.assertEqual(traps[0].trap_type, "temporal_lock")
        self.assertEqual(traps[0].severity, "high")
        self.assertEqual(len(traps[0].related_signals), 2)
        signal_types = [s["type"] for s in traps[0].related_signals]
        self.assertIn("AUTO_RENEWAL", signal_types)
        self.assertIn("SHORT_NOTICE_WINDOW", signal_types)
    
    def test_detect_trap_with_three_signals(self):
        """Test detection with all three temporal signals - should detect trap with high severity."""
        risk_signals = [
            {
                "type": "AUTO_RENEWAL",
                "confidence": "medium",
                "details": {}
            },
            {
                "type": "SHORT_NOTICE_WINDOW",
                "confidence": "high",
                "details": {}
            },
            {
                "type": "USER_ACTION_REQUIRED",
                "confidence": "medium",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        # Assertions
        self.assertEqual(len(traps), 1)
        self.assertEqual(traps[0].trap_type, "temporal_lock")
        self.assertEqual(traps[0].severity, "high")
        self.assertEqual(len(traps[0].related_signals), 3)
    
    def test_no_trap_without_temporal_signals(self):
        """Test that no trap is detected when there are no temporal-related signals."""
        risk_signals = [
            {
                "type": "LIABILITY_LIMITATION",
                "confidence": "high",
                "details": {}
            },
            {
                "type": "UNILATERAL_CHANGE",
                "confidence": "medium",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        # Assertions
        self.assertEqual(len(traps), 0)
    
    def test_no_trap_with_empty_signals(self):
        """Test that no trap is detected with empty risk signals."""
        risk_signals = []
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        # Assertions
        self.assertEqual(len(traps), 0)
    
    def test_risk_chain_builder(self):
        """Test that RiskChainBuilder creates correct chains for temporal lock traps."""
        risk_signals = [
            {
                "type": "AUTO_RENEWAL",
                "confidence": "medium",
                "details": {}
            },
            {
                "type": "SHORT_NOTICE_WINDOW",
                "confidence": "high",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        builder = RiskChainBuilder()
        chains = builder.build_chains(traps)
        
        # Assertions
        self.assertEqual(len(chains), 1)
        chain = chains[0]
        self.assertEqual(chain.trap_id, traps[0].trap_id)
        self.assertEqual(len(chain.steps), 3)
        self.assertEqual(chain.final_outcome, "用户失去低成本退出路径")
        
        # Check step 1
        self.assertEqual(chain.steps[0]["description"], "用户错过操作窗口")
        self.assertEqual(chain.steps[0]["severity"], "low")
        self.assertEqual(chain.steps[0]["order"], 1)
        
        # Check step 2
        self.assertEqual(chain.steps[1]["description"], "自动续约生效")
        self.assertEqual(chain.steps[1]["severity"], "medium")
        self.assertEqual(chain.steps[1]["order"], 2)
        
        # Check step 3
        self.assertEqual(chain.steps[2]["description"], "退出成本上升/合同锁死")
        self.assertEqual(chain.steps[2]["severity"], "high")
        self.assertEqual(chain.steps[2]["order"], 3)
    
    def test_detect_asymmetric_power_trap_with_single_signal(self):
        """Test detection with UNILATERAL_MODIFICATION signal only - should detect trap with medium severity."""
        risk_signals = [
            {
                "type": "UNILATERAL_MODIFICATION",
                "confidence": "high",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        # Assertions
        self.assertEqual(len(traps), 1)
        self.assertEqual(traps[0].trap_type, "asymmetric_power")
        self.assertEqual(traps[0].severity, "medium")
        self.assertEqual(len(traps[0].related_signals), 1)
        self.assertEqual(traps[0].related_signals[0]["type"], "UNILATERAL_MODIFICATION")
    
    def test_detect_asymmetric_power_trap_with_two_signals(self):
        """Test detection with UNILATERAL_MODIFICATION + SILENT_ACCEPTANCE - should detect trap with high severity."""
        risk_signals = [
            {
                "type": "UNILATERAL_MODIFICATION",
                "confidence": "high",
                "details": {}
            },
            {
                "type": "SILENT_ACCEPTANCE",
                "confidence": "medium",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        # Assertions
        self.assertEqual(len(traps), 1)
        self.assertEqual(traps[0].trap_type, "asymmetric_power")
        self.assertEqual(traps[0].severity, "high")
        self.assertEqual(len(traps[0].related_signals), 2)
        signal_types = [s["type"] for s in traps[0].related_signals]
        self.assertIn("UNILATERAL_MODIFICATION", signal_types)
        self.assertIn("SILENT_ACCEPTANCE", signal_types)
    
    def test_detect_asymmetric_power_trap_with_three_signals(self):
        """Test detection with all three asymmetric power signals - should detect trap with high severity."""
        risk_signals = [
            {
                "type": "UNILATERAL_MODIFICATION",
                "confidence": "high",
                "details": {}
            },
            {
                "type": "SILENT_ACCEPTANCE",
                "confidence": "medium",
                "details": {}
            },
            {
                "type": "FINAL_INTERPRETATION_RIGHT",
                "confidence": "high",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        # Assertions - FINAL_INTERPRETATION_RIGHT is shared between asymmetric_power and interpretation_ambiguity
        # So we should detect both trap types
        self.assertGreaterEqual(len(traps), 1)
        asymmetric_traps = [t for t in traps if t.trap_type == "asymmetric_power"]
        self.assertEqual(len(asymmetric_traps), 1)
        self.assertEqual(asymmetric_traps[0].severity, "high")
        self.assertEqual(len(asymmetric_traps[0].related_signals), 3)
    
    def test_no_asymmetric_power_trap_without_related_signals(self):
        """Test that no asymmetric power trap is detected when there are no related signals."""
        risk_signals = [
            {
                "type": "LIABILITY_LIMITATION",
                "confidence": "high",
                "details": {}
            },
            {
                "type": "AUTO_RENEWAL",
                "confidence": "medium",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        # Assertions - should only detect temporal_lock trap, not asymmetric_power
        self.assertEqual(len(traps), 1)
        self.assertEqual(traps[0].trap_type, "temporal_lock")
        self.assertNotEqual(traps[0].trap_type, "asymmetric_power")
    
    def test_asymmetric_power_risk_chain_builder(self):
        """Test that RiskChainBuilder creates correct chains for asymmetric power traps."""
        risk_signals = [
            {
                "type": "UNILATERAL_MODIFICATION",
                "confidence": "high",
                "details": {}
            },
            {
                "type": "SILENT_ACCEPTANCE",
                "confidence": "medium",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        builder = RiskChainBuilder()
        chains = builder.build_chains(traps)
        
        # Assertions
        self.assertEqual(len(chains), 1)
        chain = chains[0]
        self.assertEqual(chain.trap_id, traps[0].trap_id)
        self.assertEqual(len(chain.steps), 3)
        self.assertEqual(chain.final_outcome, "用户在未来争议中处于系统性劣势地位")
        
        # Check step 1
        self.assertEqual(chain.steps[0]["description"], "合同初始状态看似安全")
        self.assertEqual(chain.steps[0]["severity"], "low")
        self.assertEqual(chain.steps[0]["order"], 1)
        
        # Check step 2
        self.assertEqual(chain.steps[1]["description"], "对方单方面调整条款")
        self.assertEqual(chain.steps[1]["severity"], "medium")
        self.assertEqual(chain.steps[1]["order"], 2)
        
        # Check step 3
        self.assertEqual(chain.steps[2]["description"], "争议发生时用户处于劣势")
        self.assertEqual(chain.steps[2]["severity"], "high")
        self.assertEqual(chain.steps[2]["order"], 3)
    
    def test_both_trap_types_detected_independently(self):
        """Test that both trap types can be detected independently without interference."""
        risk_signals = [
            {
                "type": "AUTO_RENEWAL",
                "confidence": "medium",
                "details": {}
            },
            {
                "type": "UNILATERAL_MODIFICATION",
                "confidence": "high",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        # Assertions - should detect both trap types
        self.assertEqual(len(traps), 2)
        
        trap_types = [t.trap_type for t in traps]
        self.assertIn("temporal_lock", trap_types)
        self.assertIn("asymmetric_power", trap_types)
        
        # Check temporal_lock trap
        temporal_trap = next(t for t in traps if t.trap_type == "temporal_lock")
        self.assertEqual(temporal_trap.severity, "low")
        self.assertEqual(len(temporal_trap.related_signals), 1)
        
        # Check asymmetric_power trap
        asymmetric_trap = next(t for t in traps if t.trap_type == "asymmetric_power")
        self.assertEqual(asymmetric_trap.severity, "medium")
        self.assertEqual(len(asymmetric_trap.related_signals), 1)
    
    def test_detect_exit_barrier_trap_with_single_signal(self):
        """Test detection with HIGH_TERMINATION_FEE signal only - should detect trap with medium severity."""
        risk_signals = [
            {
                "type": "HIGH_TERMINATION_FEE",
                "confidence": "high",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        # Assertions
        self.assertEqual(len(traps), 1)
        self.assertEqual(traps[0].trap_type, "exit_barrier")
        self.assertEqual(traps[0].severity, "medium")
        self.assertEqual(len(traps[0].related_signals), 1)
        self.assertEqual(traps[0].related_signals[0]["type"], "HIGH_TERMINATION_FEE")
    
    def test_detect_exit_barrier_trap_with_two_signals(self):
        """Test detection with HIGH_TERMINATION_FEE + PENALTY_ESCALATION - should detect trap with high severity."""
        risk_signals = [
            {
                "type": "HIGH_TERMINATION_FEE",
                "confidence": "high",
                "details": {}
            },
            {
                "type": "PENALTY_ESCALATION",
                "confidence": "medium",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        # Assertions
        self.assertEqual(len(traps), 1)
        self.assertEqual(traps[0].trap_type, "exit_barrier")
        self.assertEqual(traps[0].severity, "high")
        self.assertEqual(len(traps[0].related_signals), 2)
        signal_types = [s["type"] for s in traps[0].related_signals]
        self.assertIn("HIGH_TERMINATION_FEE", signal_types)
        self.assertIn("PENALTY_ESCALATION", signal_types)
    
    def test_detect_exit_barrier_trap_with_three_signals(self):
        """Test detection with all three exit barrier signals - should detect trap with high severity."""
        risk_signals = [
            {
                "type": "HIGH_TERMINATION_FEE",
                "confidence": "high",
                "details": {}
            },
            {
                "type": "PENALTY_ESCALATION",
                "confidence": "medium",
                "details": {}
            },
            {
                "type": "EXIT_CONDITION_RESTRICTION",
                "confidence": "high",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        # Assertions
        self.assertEqual(len(traps), 1)
        self.assertEqual(traps[0].trap_type, "exit_barrier")
        self.assertEqual(traps[0].severity, "high")
        self.assertEqual(len(traps[0].related_signals), 3)
    
    def test_no_exit_barrier_trap_without_related_signals(self):
        """Test that no exit barrier trap is detected when there are no related signals."""
        risk_signals = [
            {
                "type": "LIABILITY_LIMITATION",
                "confidence": "high",
                "details": {}
            },
            {
                "type": "AUTO_RENEWAL",
                "confidence": "medium",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        # Assertions - should only detect temporal_lock trap, not exit_barrier
        self.assertEqual(len(traps), 1)
        self.assertEqual(traps[0].trap_type, "temporal_lock")
        self.assertNotEqual(traps[0].trap_type, "exit_barrier")
    
    def test_exit_barrier_risk_chain_builder(self):
        """Test that RiskChainBuilder creates correct chains for exit barrier traps."""
        risk_signals = [
            {
                "type": "HIGH_TERMINATION_FEE",
                "confidence": "high",
                "details": {}
            },
            {
                "type": "PENALTY_ESCALATION",
                "confidence": "medium",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        builder = RiskChainBuilder()
        chains = builder.build_chains(traps)
        
        # Assertions
        self.assertEqual(len(chains), 1)
        chain = chains[0]
        self.assertEqual(chain.trap_id, traps[0].trap_id)
        self.assertEqual(len(chain.steps), 3)
        self.assertEqual(chain.final_outcome, "用户在尝试退出合同时遭遇系统性退出障碍，导致被迫承担显著经济损失")
        
        # Check step 1
        self.assertEqual(chain.steps[0]["description"], "合同初始阶段看似可自由退出")
        self.assertEqual(chain.steps[0]["severity"], "low")
        self.assertEqual(chain.steps[0]["order"], 1)
        
        # Check step 2
        self.assertEqual(chain.steps[1]["description"], "用户尝试退出时触发高额限制或费用")
        self.assertEqual(chain.steps[1]["severity"], "medium")
        self.assertEqual(chain.steps[1]["order"], 2)
        
        # Check step 3
        self.assertEqual(chain.steps[2]["description"], "用户被迫继续履约或承担显著损失")
        self.assertEqual(chain.steps[2]["severity"], "high")
        self.assertEqual(chain.steps[2]["order"], 3)
    
    def test_all_three_trap_types_detected_independently(self):
        """Test that all three trap types can be detected independently without interference."""
        risk_signals = [
            {
                "type": "AUTO_RENEWAL",
                "confidence": "medium",
                "details": {}
            },
            {
                "type": "UNILATERAL_MODIFICATION",
                "confidence": "high",
                "details": {}
            },
            {
                "type": "HIGH_TERMINATION_FEE",
                "confidence": "high",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        # Assertions - should detect all three trap types
        self.assertEqual(len(traps), 3)
        
        trap_types = [t.trap_type for t in traps]
        self.assertIn("temporal_lock", trap_types)
        self.assertIn("asymmetric_power", trap_types)
        self.assertIn("exit_barrier", trap_types)
        
        # Check temporal_lock trap
        temporal_trap = next(t for t in traps if t.trap_type == "temporal_lock")
        self.assertEqual(temporal_trap.severity, "low")
        self.assertEqual(len(temporal_trap.related_signals), 1)
        
        # Check asymmetric_power trap
        asymmetric_trap = next(t for t in traps if t.trap_type == "asymmetric_power")
        self.assertEqual(asymmetric_trap.severity, "medium")
        self.assertEqual(len(asymmetric_trap.related_signals), 1)
        
        # Check exit_barrier trap
        exit_barrier_trap = next(t for t in traps if t.trap_type == "exit_barrier")
        self.assertEqual(exit_barrier_trap.severity, "medium")
        self.assertEqual(len(exit_barrier_trap.related_signals), 1)
    
    def test_detect_interpretation_ambiguity_trap_with_single_signal(self):
        """Test detection with AMBIGUOUS_TERM signal only - should detect trap with medium severity."""
        risk_signals = [
            {
                "type": "AMBIGUOUS_TERM",
                "confidence": "high",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        # Assertions
        self.assertEqual(len(traps), 1)
        self.assertEqual(traps[0].trap_type, "interpretation_ambiguity")
        self.assertEqual(traps[0].severity, "medium")
        self.assertEqual(len(traps[0].related_signals), 1)
        self.assertEqual(traps[0].related_signals[0]["type"], "AMBIGUOUS_TERM")
    
    def test_detect_interpretation_ambiguity_trap_with_two_signals(self):
        """Test detection with AMBIGUOUS_TERM + SUBJECTIVE_CRITERIA - should detect trap with high severity."""
        risk_signals = [
            {
                "type": "AMBIGUOUS_TERM",
                "confidence": "high",
                "details": {}
            },
            {
                "type": "SUBJECTIVE_CRITERIA",
                "confidence": "medium",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        # Assertions
        self.assertEqual(len(traps), 1)
        self.assertEqual(traps[0].trap_type, "interpretation_ambiguity")
        self.assertEqual(traps[0].severity, "high")
        self.assertEqual(len(traps[0].related_signals), 2)
        signal_types = [s["type"] for s in traps[0].related_signals]
        self.assertIn("AMBIGUOUS_TERM", signal_types)
        self.assertIn("SUBJECTIVE_CRITERIA", signal_types)
    
    def test_detect_interpretation_ambiguity_trap_with_three_signals(self):
        """Test detection with all three interpretation ambiguity signals - should detect trap with high severity."""
        risk_signals = [
            {
                "type": "AMBIGUOUS_TERM",
                "confidence": "high",
                "details": {}
            },
            {
                "type": "SUBJECTIVE_CRITERIA",
                "confidence": "medium",
                "details": {}
            },
            {
                "type": "FINAL_INTERPRETATION_RIGHT",
                "confidence": "high",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        # Assertions - should detect both interpretation_ambiguity and asymmetric_power (FINAL_INTERPRETATION_RIGHT is shared)
        self.assertGreaterEqual(len(traps), 1)
        interpretation_traps = [t for t in traps if t.trap_type == "interpretation_ambiguity"]
        self.assertEqual(len(interpretation_traps), 1)
        self.assertEqual(interpretation_traps[0].severity, "high")
        self.assertEqual(len(interpretation_traps[0].related_signals), 3)
    
    def test_no_interpretation_ambiguity_trap_without_related_signals(self):
        """Test that no interpretation ambiguity trap is detected when there are no related signals."""
        risk_signals = [
            {
                "type": "LIABILITY_LIMITATION",
                "confidence": "high",
                "details": {}
            },
            {
                "type": "AUTO_RENEWAL",
                "confidence": "medium",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        # Assertions - should only detect temporal_lock trap, not interpretation_ambiguity
        self.assertEqual(len(traps), 1)
        self.assertEqual(traps[0].trap_type, "temporal_lock")
        self.assertNotEqual(traps[0].trap_type, "interpretation_ambiguity")
    
    def test_interpretation_ambiguity_risk_chain_builder(self):
        """Test that RiskChainBuilder creates correct chains for interpretation ambiguity traps."""
        risk_signals = [
            {
                "type": "AMBIGUOUS_TERM",
                "confidence": "high",
                "details": {}
            },
            {
                "type": "SUBJECTIVE_CRITERIA",
                "confidence": "medium",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        builder = RiskChainBuilder()
        chains = builder.build_chains(traps)
        
        # Assertions
        self.assertEqual(len(chains), 1)
        chain = chains[0]
        self.assertEqual(chain.trap_id, traps[0].trap_id)
        self.assertEqual(len(chain.steps), 3)
        self.assertEqual(chain.final_outcome, "用户因合同条款解释权不对等，在实际执行或争议中处于系统性不利地位")
        
        # Check step 1
        self.assertEqual(chain.steps[0]["description"], "合同条款在签署时看似灵活或无明显风险")
        self.assertEqual(chain.steps[0]["severity"], "low")
        self.assertEqual(chain.steps[0]["order"], 1)
        
        # Check step 2
        self.assertEqual(chain.steps[1]["description"], "实际执行中条款含义被单方面解释")
        self.assertEqual(chain.steps[1]["severity"], "medium")
        self.assertEqual(chain.steps[1]["order"], 2)
        
        # Check step 3
        self.assertEqual(chain.steps[2]["description"], "争议发生时用户因解释权劣势承担不利后果")
        self.assertEqual(chain.steps[2]["severity"], "high")
        self.assertEqual(chain.steps[2]["order"], 3)
    
    def test_all_four_trap_types_detected_independently(self):
        """Test that all four trap types can be detected independently without interference."""
        risk_signals = [
            {
                "type": "AUTO_RENEWAL",
                "confidence": "medium",
                "details": {}
            },
            {
                "type": "UNILATERAL_MODIFICATION",
                "confidence": "high",
                "details": {}
            },
            {
                "type": "HIGH_TERMINATION_FEE",
                "confidence": "high",
                "details": {}
            },
            {
                "type": "AMBIGUOUS_TERM",
                "confidence": "high",
                "details": {}
            }
        ]
        
        engine = TrapEngineV2(risk_signals)
        traps = engine.detect_traps()
        
        # Assertions - should detect all four trap types
        self.assertEqual(len(traps), 4)
        
        trap_types = [t.trap_type for t in traps]
        self.assertIn("temporal_lock", trap_types)
        self.assertIn("asymmetric_power", trap_types)
        self.assertIn("exit_barrier", trap_types)
        self.assertIn("interpretation_ambiguity", trap_types)
        
        # Check temporal_lock trap
        temporal_trap = next(t for t in traps if t.trap_type == "temporal_lock")
        self.assertEqual(temporal_trap.severity, "low")
        self.assertEqual(len(temporal_trap.related_signals), 1)
        
        # Check asymmetric_power trap
        asymmetric_trap = next(t for t in traps if t.trap_type == "asymmetric_power")
        self.assertEqual(asymmetric_trap.severity, "medium")
        self.assertEqual(len(asymmetric_trap.related_signals), 1)
        
        # Check exit_barrier trap
        exit_barrier_trap = next(t for t in traps if t.trap_type == "exit_barrier")
        self.assertEqual(exit_barrier_trap.severity, "medium")
        self.assertEqual(len(exit_barrier_trap.related_signals), 1)
        
        # Check interpretation_ambiguity trap
        interpretation_trap = next(t for t in traps if t.trap_type == "interpretation_ambiguity")
        self.assertEqual(interpretation_trap.severity, "medium")
        self.assertEqual(len(interpretation_trap.related_signals), 1)


if __name__ == '__main__':
    unittest.main()

