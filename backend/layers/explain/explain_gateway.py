"""
Explain Gateway
===============
Gateway for aggregating and encapsulating explanations from v0, v1, and v2.

Gateway Responsibilities (strictly limited):
- Aggregation: Collect outputs from v0, v1, v2
- Sorting: Sort results if needed
- Filtering: Filter results if needed
- Encapsulation: Wrap into unified GatewayOutput structure

Gateway Constraints:
- Gateway does NOT own worldview
- Gateway does NOT validate Explain v2 logic
- Gateway does NOT understand Explain v2 content
- Gateway does NOT modify Explain v2 fields
- Gateway treats Explain v2 as "trusted but immutable black box"

Gateway Output Structure (immutable):
{
  "overview": {...},
  "key_findings": [...],
  "next_actions": [...],
  "details": {...}
}
"""

from typing import Optional, Dict, Any, List
from models.data_models import (
    ExplanationOutput,
    ExplanationOutputV1,
    ExplainV2Output,
    GatewayOutput
)


class ExplainGateway:
    """
    Gateway for aggregating explanations from v0, v1, and v2.
    
    This gateway only performs aggregation, sorting, filtering, and encapsulation.
    It does NOT interpret, validate, or modify explanation content.
    """
    
    def aggregate(
        self,
        explain_v0_output: Optional[ExplanationOutput] = None,
        explain_v1_output: Optional[ExplanationOutputV1] = None,
        explain_v2_output: Optional[ExplainV2Output] = None
    ) -> GatewayOutput:
        """
        Aggregate explanations from v0, v1, and v2 into GatewayOutput.
        
        Gateway does NOT:
        - Interpret explanation content
        - Validate explanation logic
        - Modify explanation fields
        - Infer missing fields
        - Optimize or merge explanations
        
        Gateway only:
        - Aggregates outputs (pass-through)
        - Encapsulates into GatewayOutput structure
        - Preserves all fields as-is
        
        Args:
            explain_v0_output: Optional v0 explanation output
            explain_v1_output: Optional v1 explanation output
            explain_v2_output: Optional v2 explanation output (treated as black box)
            
        Returns:
            GatewayOutput with strictly defined structure
        """
        # Aggregate overview (simple aggregation, no inference)
        overview = self._build_overview(
            explain_v0_output=explain_v0_output,
            explain_v1_output=explain_v1_output,
            explain_v2_output=explain_v2_output
        )
        
        # Aggregate key findings (pass-through, no interpretation)
        key_findings = self._build_key_findings(
            explain_v0_output=explain_v0_output,
            explain_v1_output=explain_v1_output,
            explain_v2_output=explain_v2_output
        )
        
        # Aggregate next actions (pass-through, no interpretation)
        next_actions = self._build_next_actions(
            explain_v0_output=explain_v0_output,
            explain_v1_output=explain_v1_output,
            explain_v2_output=explain_v2_output
        )
        
        # Aggregate details (pass-through, no interpretation)
        details = self._build_details(
            explain_v0_output=explain_v0_output,
            explain_v1_output=explain_v1_output,
            explain_v2_output=explain_v2_output
        )
        
        return GatewayOutput(
            overview=overview,
            key_findings=key_findings,
            next_actions=next_actions,
            details=details
        )
    
    def _build_overview(
        self,
        explain_v0_output: Optional[ExplanationOutput],
        explain_v1_output: Optional[ExplanationOutputV1],
        explain_v2_output: Optional[ExplainV2Output]
    ) -> Dict[str, Any]:
        """
        Build overview section.
        
        Gateway aggregates to produce:
        - attention_level: highest level from v2/v1/v0
        - summary: one-sentence judgment (prefer v2 headline, fallback to v1/v0)
        """
        overview: Dict[str, Any] = {}
        
        # Determine attention_level (aggregate from available sources)
        attention_level = "low"
        if explain_v2_output:
            # Map confidence_level to attention: high->high, medium->medium, low->low
            attention_level = explain_v2_output.confidence_level.value
        elif explain_v1_output and explain_v1_output.risk_field_explanations:
            # Use highest intensity from v1
            intensities = [exp.intensity for exp in explain_v1_output.risk_field_explanations]
            if "high" in intensities:
                attention_level = "high"
            elif "medium" in intensities:
                attention_level = "medium"
        elif explain_v0_output and explain_v0_output.explanation_blocks:
            # Use highest severity from v0
            severities = [block.severity for block in explain_v0_output.explanation_blocks]
            if "high" in severities:
                attention_level = "high"
            elif "medium" in severities:
                attention_level = "medium"
        
        # Determine summary (one-sentence judgment)
        summary = ""
        if explain_v2_output:
            summary = explain_v2_output.headline
        elif explain_v1_output and explain_v1_output.risk_field_explanations:
            # Use first v1 title as summary
            summary = explain_v1_output.risk_field_explanations[0].title
        elif explain_v0_output:
            summary = explain_v0_output.overall_message
        
        overview["attention_level"] = attention_level
        overview["summary"] = summary
        
        return overview
    
    def _build_key_findings(
        self,
        explain_v0_output: Optional[ExplanationOutput],
        explain_v1_output: Optional[ExplanationOutputV1],
        explain_v2_output: Optional[ExplainV2Output]
    ) -> List[Dict[str, Any]]:
        """
        Build key findings section.
        
        Gateway aggregates and orders by v2 → v1 → v0, with compression.
        """
        key_findings: List[Dict[str, Any]] = []
        
        # Aggregate v2 findings first (highest priority)
        if explain_v2_output:
            key_findings.append({
                "source": "v2",
                "headline": explain_v2_output.headline,
                "core_logic": explain_v2_output.core_logic,
                "power_map": explain_v2_output.power_map,
                "mechanism": explain_v2_output.mechanism.value
            })
        
        # Aggregate v1 findings (medium priority)
        if explain_v1_output:
            # Limit v1 findings (take first 2 if available)
            v1_count = min(2, len(explain_v1_output.risk_field_explanations))
            for exp in explain_v1_output.risk_field_explanations[:v1_count]:
                key_findings.append({
                    "source": "v1",
                    "title": exp.title,
                    "message": exp.message,
                    "axis": exp.axis.value,
                    "intensity": exp.intensity,
                    "affected_party": exp.affected_party
                })
        
        # Aggregate v0 findings last (lowest priority)
        if explain_v0_output:
            # Limit v0 findings (take first 1 if available, only if we have space)
            max_total = 4  # Total limit
            remaining_slots = max_total - len(key_findings)
            if remaining_slots > 0:
                v0_count = min(remaining_slots, len(explain_v0_output.explanation_blocks))
                for block in explain_v0_output.explanation_blocks[:v0_count]:
                    key_findings.append({
                        "source": "v0",
                        "title": block.title,
                        "message": block.message,
                        "severity": block.severity,
                        "risk_code": block.risk_code
                    })
        
        return key_findings
    
    def _build_next_actions(
        self,
        explain_v0_output: Optional[ExplanationOutput],
        explain_v1_output: Optional[ExplanationOutputV1],
        explain_v2_output: Optional[ExplainV2Output]
    ) -> List[Dict[str, Any]]:
        """
        Build next actions section.
        
        Gateway aggregates and filters:
        - Maximum 2 actions
        - Remove legal advice or refusal to sign language
        - Priority: v2 → v1 → v0
        """
        next_actions: List[Dict[str, Any]] = []
        
        # Keywords to filter out (legal advice / refusal language)
        filter_keywords = [
            "法律建议",
            "拒绝签署",
            "寻求法律建议",
            "legal advice",
            "refuse to sign",
            "seek legal",
            "consult a lawyer",
            "拒绝",
            "建议寻求"
        ]
        
        def should_filter(action_text: str) -> bool:
            """Check if action contains filtered keywords."""
            action_lower = action_text.lower()
            for keyword in filter_keywords:
                if keyword.lower() in action_lower:
                    return True
            return False
        
        # Aggregate v2 actions first (highest priority)
        if explain_v2_output:
            for action in explain_v2_output.user_actions:
                if not should_filter(action):
                    next_actions.append({
                        "source": "v2",
                        "action": action,
                        "mechanism": explain_v2_output.mechanism.value
                    })
                    if len(next_actions) >= 2:
                        break
        
        # Aggregate v1 actions (medium priority)
        if explain_v1_output and len(next_actions) < 2:
            for exp in explain_v1_output.risk_field_explanations:
                if not should_filter(exp.user_action):
                    next_actions.append({
                        "source": "v1",
                        "action": exp.user_action,
                        "axis": exp.axis.value
                    })
                    if len(next_actions) >= 2:
                        break
        
        # Aggregate v0 actions last (lowest priority)
        if explain_v0_output and len(next_actions) < 2:
            for block in explain_v0_output.explanation_blocks:
                if not should_filter(block.user_action):
                    next_actions.append({
                        "source": "v0",
                        "action": block.user_action,
                        "risk_code": block.risk_code
                    })
                    if len(next_actions) >= 2:
                        break
        
        return next_actions
    
    def _build_details(
        self,
        explain_v0_output: Optional[ExplanationOutput],
        explain_v1_output: Optional[ExplanationOutputV1],
        explain_v2_output: Optional[ExplainV2Output]
    ) -> Dict[str, Any]:
        """
        Build details section.
        
        Gateway only aggregates existing fields, no inference or interpretation.
        """
        details: Dict[str, Any] = {}
        
        # Aggregate v0 details (pass-through)
        if explain_v0_output:
            details["v0"] = {
                "explanation_blocks": [
                    {
                        "title": block.title,
                        "message": block.message,
                        "user_action": block.user_action,
                        "severity": block.severity,
                        "risk_code": block.risk_code
                    }
                    for block in explain_v0_output.explanation_blocks
                ]
            }
        
        # Aggregate v1 details (pass-through)
        if explain_v1_output:
            details["v1"] = {
                "risk_field_explanations": [
                    {
                        "axis": exp.axis.value,
                        "intensity": exp.intensity,
                        "affected_party": exp.affected_party,
                        "title": exp.title,
                        "message": exp.message,
                        "user_action": exp.user_action,
                        "compounding": exp.compounding,
                        "source_blocks": exp.source_blocks
                    }
                    for exp in explain_v1_output.risk_field_explanations
                ]
            }
        
        # Aggregate v2 details (pass-through - treat as black box, no interpretation)
        if explain_v2_output:
            v2_detail: Dict[str, Any] = {
                "mechanism": explain_v2_output.mechanism.value,
                "headline": explain_v2_output.headline,
                "core_logic": explain_v2_output.core_logic,
                "power_map": explain_v2_output.power_map,
                "irreversibility": explain_v2_output.irreversibility.value,
                "escape_window": explain_v2_output.escape_window,
                "user_actions": explain_v2_output.user_actions,
                "confidence_level": explain_v2_output.confidence_level.value
            }
            # Include lock_in_dynamics only if present (for Temporal Lock-in)
            if explain_v2_output.lock_in_dynamics:
                v2_detail["lock_in_dynamics"] = {
                    "description": explain_v2_output.lock_in_dynamics.description
                }
            details["v2"] = v2_detail
        
        return details

