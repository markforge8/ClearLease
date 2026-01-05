# run_gateway_json_output.py
# End-to-end flow: Contract -> Gateway JSON output

import sys
import os
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from backend.layers.ingestion.ingestion_service import IngestionService
from backend.layers.extraction.extraction_service import ExtractionService
from backend.layers.analysis.analysis_service import AnalysisService
from backend.models.data_models import IngestionInput, AnalysisInput
from backend.layers.explain.explain_service import ExplainService
from backend.layers.explain.explain_v1_service import ExplainV1Service
from backend.layers.explain.explain_v2_service import ExplainV2Service
from backend.layers.explain.explain_gateway import ExplainGateway
from backend.models.data_models import (
    ExplainV2Input,
    TrapType,
    Strength,
    Beneficiary,
    Irreversibility
)


def build_explain_v2_input_from_contract(contract_text: str, analysis_output) -> ExplainV2Input:
    """
    Build ExplainV2Input from contract analysis (simplified for MVP).
    
    In MVP phase, this is a simplified converter.
    In production, this would come from Analysis v2 trap detection.
    
    For MVP, we detect Temporal Lock-in based on:
    - Contract text contains "automatically renew" or "automatic renewal"
    - Contract text contains notice period (e.g., "90 days", "30 days")
    """
    # Simple detection for MVP
    contract_lower = contract_text.lower()
    has_auto_renewal = any(keyword in contract_lower for keyword in [
        "automatically renew",
        "automatic renewal",
        "auto renew",
        "shall automatically renew"
    ])
    
    has_notice_period = any(keyword in contract_lower for keyword in [
        "90 days",
        "30 days",
        "60 days",
        "notice of termination",
        "written notice"
    ])
    
    # Determine strength based on signals
    if has_auto_renewal and has_notice_period:
        strength = Strength.HIGH
    elif has_auto_renewal:
        strength = Strength.MEDIUM
    else:
        strength = Strength.LOW
    
    # Extract notice period if available
    notice_text = ""
    deadline_text = ""
    if "90 days" in contract_lower:
        deadline_text = "合同到期前90天"
        notice_text = "在续约窗口关闭前提供书面终止通知"
    elif "30 days" in contract_lower:
        deadline_text = "合同到期前30天"
        notice_text = "在续约窗口关闭前提供书面终止通知"
    elif "60 days" in contract_lower:
        deadline_text = "合同到期前60天"
        notice_text = "在续约窗口关闭前提供书面终止通知"
    else:
        deadline_text = "合同到期前"
        notice_text = "在续约窗口关闭前提供书面终止通知"
    
    return ExplainV2Input(
        trap_type=TrapType.TEMPORAL_LOCK_IN,
        strength=strength,
        beneficiary=Beneficiary.COUNTERPARTY,
        cost_bearer="user",
        irreversibility=Irreversibility.PARTIALLY_REVERSIBLE,
        evidence={
            "signals": ["AUTO_RENEWAL", "SHORT_NOTICE_WINDOW"] if has_notice_period else ["AUTO_RENEWAL"],
            "clause_references": ["续约条款", "通知条款"] if has_notice_period else ["续约条款"]
        },
        window={
            "exists": True,
            "conditions": notice_text,
            "deadline": deadline_text
        }
    )


def run_end_to_end(contract_text: str):
    """
    Run end-to-end flow: Contract -> Gateway JSON output
    """
    # 1. Ingestion
    ingestion_service = IngestionService()
    ingestion_result = ingestion_service.ingest(IngestionInput(text=contract_text))
    
    # 2. Extraction
    extraction_service = ExtractionService()
    extraction_candidates = extraction_service.extract(ingestion_result.text_blocks)
    extraction_result = []
    for idx, candidate in enumerate(extraction_candidates):
        from backend.models.data_models import ExtractedSignal
        signal = ExtractedSignal(
            rule_id=candidate.rule_id,
            type=candidate.rule_type,
            hit_text=candidate.extracted_text,
            block_id=candidate.block_id,
            order=idx
        )
        extraction_result.append(signal)
    
    # 3. Analysis (v0 + v1)
    analysis_service = AnalysisService()
    analysis_input = AnalysisInput(
        doc_id="demo_doc",
        extracted_signals=extraction_result
    )
    analysis_output = analysis_service.analyze(analysis_input)
    
    # 4. Explain v0
    explain_service_v0 = ExplainService()
    explain_v0_result = explain_service_v0.explain(analysis_output)
    
    # 5. Explain v1
    explain_service_v1 = ExplainV1Service()
    explain_v1_result = explain_service_v1.explain(analysis_output.risk_fields)
    
    # 6. Explain v2 (real implementation, only Temporal Lock-in)
    explain_service_v2 = ExplainV2Service()
    explain_v2_input = build_explain_v2_input_from_contract(contract_text, analysis_output)
    
    # Only call Explain v2 if we detected Temporal Lock-in signals
    explain_v2_result = None
    contract_lower = contract_text.lower()
    has_temporal_signals = any(keyword in contract_lower for keyword in [
        "automatically renew",
        "automatic renewal",
        "auto renew"
    ])
    
    if has_temporal_signals:
        try:
            explain_v2_result = explain_service_v2.explain(explain_v2_input)
        except ValueError as e:
            # If trap type not supported, skip v2
            print(f"Explain v2 skipped: {e}")
    
    # 7. Gateway aggregation
    gateway = ExplainGateway()
    gateway_output = gateway.aggregate(
        explain_v0_output=explain_v0_result,
        explain_v1_output=explain_v1_result,
        explain_v2_output=explain_v2_result
    )
    
    return gateway_output


def output_gateway_json(gateway_output, output_file: str = None):
    """
    Output Gateway JSON to file or stdout
    """
    # Convert to dict for JSON serialization
    gateway_dict = {
        "overview": gateway_output.overview,
        "key_findings": gateway_output.key_findings,
        "next_actions": gateway_output.next_actions,
        "details": gateway_output.details
    }
    
    json_str = json.dumps(gateway_dict, ensure_ascii=False, indent=2)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_str)
        print(f"Gateway JSON output written to: {output_file}")
    else:
        print("\n" + "=" * 80)
        print("GATEWAY JSON OUTPUT")
        print("=" * 80)
        print(json_str)
        print("=" * 80)


if __name__ == "__main__":
    # Test contract with auto-renewal clause
    TEST_CONTRACT_WITH_AUTO_RENEWAL = """
    This lease shall automatically renew for successive one-year terms unless Tenant provides
    written notice of termination at least 90 days prior to the end of the current term.
    Early termination by Tenant shall result in a penalty equal to the remaining rent due.
    """
    
    # Run end-to-end flow
    gateway_output = run_end_to_end(TEST_CONTRACT_WITH_AUTO_RENEWAL)
    
    # Output Gateway JSON
    output_gateway_json(gateway_output, output_file="gateway_output.json")
    
    # Also print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Attention Level: {gateway_output.overview.get('attention_level', 'N/A')}")
    print(f"Summary: {gateway_output.overview.get('summary', 'N/A')}")
    print(f"Key Findings Count: {len(gateway_output.key_findings)}")
    print(f"Next Actions Count: {len(gateway_output.next_actions)}")
    print("=" * 80)


