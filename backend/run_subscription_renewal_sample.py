# run_subscription_renewal_sample.py
# Process subscription renewal confirmation dialog

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
    Build ExplainV2Input from contract analysis.
    Detects Temporal Lock-in based on auto-renewal clauses.
    """
    contract_lower = contract_text.lower()
    
    # Detect auto-renewal
    has_auto_renewal = any(keyword in contract_lower for keyword in [
        "automatically renew",
        "automatic renewal",
        "auto renew",
        "自动续订",
        "自动续费",
        "自动续约"
    ])
    
    # Detect specific renewal date
    has_renewal_date = any(keyword in contract_lower for keyword in [
        "will automatically renew on",
        "auto-renewal date",
        "自动续订日期",
        "将于",
        "自动续订"
    ])
    
    # Determine strength
    if has_auto_renewal and has_renewal_date:
        strength = Strength.HIGH
    elif has_auto_renewal:
        strength = Strength.MEDIUM
    else:
        strength = Strength.LOW
    
    # Extract renewal date if available
    import re
    date_patterns = [
        r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日",
        r"(\d{4})-(\d{1,2})-(\d{1,2})",
        r"(january|february|march|april|may|june|july|august|september|october|november|december)\s*(\d{1,2}),?\s*(\d{4})"
    ]
    
    deadline_text = ""
    notice_text = ""
    
    for pattern in date_patterns:
        match = re.search(pattern, contract_text, re.IGNORECASE)
        if match:
            if "年" in contract_text:
                deadline_text = match.group(0)
            else:
                deadline_text = match.group(0)
            break
    
    if has_renewal_date and deadline_text:
        notice_text = f"在自动续订日期前（{deadline_text}）取消订阅，否则将自动续订"
    elif has_auto_renewal:
        notice_text = "在服务到期前取消自动续订服务"
        if not deadline_text:
            deadline_text = "服务到期前"
    else:
        notice_text = "在服务到期前取消服务"
        deadline_text = "服务到期前"
    
    return ExplainV2Input(
        trap_type=TrapType.TEMPORAL_LOCK_IN,
        strength=strength,
        beneficiary=Beneficiary.PROVIDER,
        cost_bearer="user",
        irreversibility=Irreversibility.PARTIALLY_REVERSIBLE,
        evidence={
            "signals": ["AUTO_RENEWAL", "RENEWAL_DATE"] if has_renewal_date else ["AUTO_RENEWAL"],
            "clause_references": ["自动续订条款", "续订日期条款"] if has_renewal_date else ["自动续订条款"]
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
        doc_id="subscription_renewal_sample",
        extracted_signals=extraction_result
    )
    analysis_output = analysis_service.analyze(analysis_input)
    
    # 4. Explain v0
    explain_service_v0 = ExplainService()
    explain_v0_result = explain_service_v0.explain(analysis_output)
    
    # 5. Explain v1
    explain_service_v1 = ExplainV1Service()
    explain_v1_result = explain_service_v1.explain(analysis_output.risk_fields)
    
    # 6. Explain v2
    explain_service_v2 = ExplainV2Service()
    explain_v2_input = build_explain_v2_input_from_contract(contract_text, analysis_output)
    
    explain_v2_result = None
    contract_lower = contract_text.lower()
    has_temporal_signals = any(keyword in contract_lower for keyword in [
        "automatically renew",
        "automatic renewal",
        "auto renew",
        "自动续订",
        "自动续费",
        "自动续约"
    ])
    
    if has_temporal_signals:
        try:
            explain_v2_result = explain_service_v2.explain(explain_v2_input)
        except ValueError as e:
            pass
    
    # 7. Gateway aggregation
    gateway = ExplainGateway()
    gateway_output = gateway.aggregate(
        explain_v0_output=explain_v0_result,
        explain_v1_output=explain_v1_result,
        explain_v2_output=explain_v2_result
    )
    
    return gateway_output


if __name__ == "__main__":
    # Extract text from subscription renewal confirmation dialog
    SUBSCRIPTION_RENEWAL_TEXT = """
    Confirm plan change (确认套餐更改)
    
    Your current Plus subscription will automatically renew on January 20, 2026.
    (你当前的 Plus 订阅将于2026年1月20日 自动续订。)
    
    ChatGPT Plus
    Billing auto-renewal date: January 20, 2026
    (结算自动续订日期: 2026年1月20日)
    
    PHP 1100 per month (PHP ₱1100/月)
    
    Cancel (取消) / Confirm (确认)
    """
    
    # Run end-to-end flow
    gateway_output = run_end_to_end(SUBSCRIPTION_RENEWAL_TEXT)
    
    # Output Gateway JSON (standard Explain v2 schema)
    gateway_dict = {
        "overview": gateway_output.overview,
        "key_findings": gateway_output.key_findings,
        "next_actions": gateway_output.next_actions,
        "details": gateway_output.details
    }
    
    # Output JSON to stdout (standard format)
    print(json.dumps(gateway_dict, ensure_ascii=False, indent=2))

