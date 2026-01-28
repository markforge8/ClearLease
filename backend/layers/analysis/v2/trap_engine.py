import uuid
from backend.models.data_models import Trap


class TrapEngineV2:
    def __init__(self, risk_signals: list):
        """
        risk_signals: output from RiskBuilderV1
        Each signal is a dict with at least:
        - type: str (e.g., "AUTO_RENEWAL", "SHORT_NOTICE_WINDOW", "USER_ACTION_REQUIRED")
        - confidence: str (e.g., "low", "medium", "high")
        - details: dict (optional additional information)
        """
        self.risk_signals = risk_signals

    def detect_traps(self) -> list:
        """
        Returns a list of detected structural traps
        
        Detects Temporal Lock-in Trap when risk_signals contain:
        - AUTO_RENEWAL
        - SHORT_NOTICE_WINDOW
        - USER_ACTION_REQUIRED
        
        Severity upgrade: if ≥ 2 signals are present
        
        Detects Asymmetric Power Trap when risk_signals contain:
        - UNILATERAL_MODIFICATION
        - SILENT_ACCEPTANCE
        - FINAL_INTERPRETATION_RIGHT
        
        Severity: 1 signal → medium, ≥2 signals → high
        
        Detects Exit Barrier Trap when risk_signals contain:
        - HIGH_TERMINATION_FEE
        - PENALTY_ESCALATION
        - EXIT_CONDITION_RESTRICTION
        
        Severity: 1 signal → medium, ≥2 signals → high
        
        Detects Interpretation / Ambiguity Trap when risk_signals contain:
        - AMBIGUOUS_TERM
        - SUBJECTIVE_CRITERIA
        - FINAL_INTERPRETATION_RIGHT
        
        Severity: 1 signal → medium, ≥2 signals → high
        """
        traps = []
        
        # Temporal Lock-in Trap detection signals
        temporal_signals = ["AUTO_RENEWAL", "SHORT_NOTICE_WINDOW", "USER_ACTION_REQUIRED"]
        
        # Find matching signals
        matched_signals = []
        for signal in self.risk_signals:
            signal_type = signal.get("type") if isinstance(signal, dict) else getattr(signal, "type", None)
            if signal_type in temporal_signals:
                matched_signals.append(signal)
        
        # If we have at least one temporal signal, create a trap
        if matched_signals:
            # Determine severity based on number of matched signals
            if len(matched_signals) >= 2:
                severity = "high"
            else:
                severity = "low"
            
            trap = Trap(
                trap_id=f"trap_{uuid.uuid4().hex[:8]}",
                trap_type="temporal_lock",
                related_signals=matched_signals,
                severity=severity
            )
            traps.append(trap)
        
        # Asymmetric Power Trap detection signals
        asymmetric_signals = ["UNILATERAL_MODIFICATION", "SILENT_ACCEPTANCE", "FINAL_INTERPRETATION_RIGHT"]
        
        # Find matching signals
        matched_asymmetric_signals = []
        for signal in self.risk_signals:
            signal_type = signal.get("type") if isinstance(signal, dict) else getattr(signal, "type", None)
            if signal_type in asymmetric_signals:
                matched_asymmetric_signals.append(signal)
        
        # If we have at least one asymmetric signal, create a trap
        if matched_asymmetric_signals:
            # Determine severity based on number of matched signals
            if len(matched_asymmetric_signals) >= 2:
                severity = "high"
            else:
                severity = "medium"
            
            trap = Trap(
                trap_id=f"trap_{uuid.uuid4().hex[:8]}",
                trap_type="asymmetric_power",
                related_signals=matched_asymmetric_signals,
                severity=severity
            )
            traps.append(trap)
        
        # Exit Barrier Trap detection signals
        exit_barrier_signals = ["HIGH_TERMINATION_FEE", "PENALTY_ESCALATION", "EXIT_CONDITION_RESTRICTION"]
        
        # Find matching signals
        matched_exit_barrier_signals = []
        for signal in self.risk_signals:
            signal_type = signal.get("type") if isinstance(signal, dict) else getattr(signal, "type", None)
            if signal_type in exit_barrier_signals:
                matched_exit_barrier_signals.append(signal)
        
        # If we have at least one exit barrier signal, create a trap
        if matched_exit_barrier_signals:
            # Determine severity based on number of matched signals
            if len(matched_exit_barrier_signals) >= 2:
                severity = "high"
            else:
                severity = "medium"
            
            trap = Trap(
                trap_id=f"trap_{uuid.uuid4().hex[:8]}",
                trap_type="exit_barrier",
                related_signals=matched_exit_barrier_signals,
                severity=severity
            )
            traps.append(trap)
        
        # Interpretation / Ambiguity Trap detection signals
        interpretation_signals = ["AMBIGUOUS_TERM", "SUBJECTIVE_CRITERIA", "FINAL_INTERPRETATION_RIGHT"]
        
        # Find matching signals
        matched_interpretation_signals = []
        for signal in self.risk_signals:
            signal_type = signal.get("type") if isinstance(signal, dict) else getattr(signal, "type", None)
            if signal_type in interpretation_signals:
                matched_interpretation_signals.append(signal)
        
        # If we have at least one interpretation signal, create a trap
        if matched_interpretation_signals:
            # Determine severity based on number of matched signals
            if len(matched_interpretation_signals) >= 2:
                severity = "high"
            else:
                severity = "medium"
            
            trap = Trap(
                trap_id=f"trap_{uuid.uuid4().hex[:8]}",
                trap_type="interpretation_ambiguity",
                related_signals=matched_interpretation_signals,
                severity=severity
            )
            traps.append(trap)
        
        return traps
