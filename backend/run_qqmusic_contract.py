# run_qqmusic_contract.py
# Process QQ Music subscription contract through full pipeline

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
        "shall automatically renew",
        "自动续费",
        "自动续约",
        "自动延长"
    ])
    
    has_notice_period = any(keyword in contract_lower for keyword in [
        "90 days",
        "30 days",
        "60 days",
        "notice of termination",
        "written notice",
        "服务到期当天",
        "关闭",
        "关闭扣费"
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
    if "服务到期当天" in contract_text or "到期当天" in contract_text:
        deadline_text = "服务到期当天"
        notice_text = "在服务到期前关闭自动续费服务"
    elif "90 days" in contract_lower:
        deadline_text = "合同到期前90天"
        notice_text = "在续约窗口关闭前提供书面终止通知"
    elif "30 days" in contract_lower:
        deadline_text = "合同到期前30天"
        notice_text = "在续约窗口关闭前提供书面终止通知"
    else:
        deadline_text = "服务到期前"
        notice_text = "在服务到期前关闭自动续费服务"
    
    return ExplainV2Input(
        trap_type=TrapType.TEMPORAL_LOCK_IN,
        strength=strength,
        beneficiary=Beneficiary.PROVIDER,  # Service provider (Tencent)
        cost_bearer="user",
        irreversibility=Irreversibility.PARTIALLY_REVERSIBLE,
        evidence={
            "signals": ["AUTO_RENEWAL", "SHORT_NOTICE_WINDOW"] if has_notice_period else ["AUTO_RENEWAL"],
            "clause_references": ["自动续费条款", "扣费条款"] if has_notice_period else ["自动续费条款"]
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
        doc_id="qqmusic_subscription",
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
        "auto renew",
        "自动续费",
        "自动续约",
        "自动延长"
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


def output_first_screen(gateway_output):
    """
    Output first screen information (overview + key findings)
    """
    print("\n" + "=" * 80)
    print("FIRST SCREEN - Risk Assessment")
    print("=" * 80)
    print(f"\n[Attention Level] {gateway_output.overview.get('attention_level', 'N/A').upper()}")
    print(f"[Summary] {gateway_output.overview.get('summary', 'N/A')}")
    
    print(f"\n[Key Findings] ({len(gateway_output.key_findings)} items)")
    for i, finding in enumerate(gateway_output.key_findings[:3], 1):  # Show first 3
        source = finding.get('source', 'unknown')
        if source == 'v2':
            print(f"\n  {i}. [{source.upper()}] {finding.get('headline', 'N/A')}")
            print(f"      Mechanism: {finding.get('mechanism', 'N/A')}")
            print(f"      Core Logic: {finding.get('core_logic', 'N/A')}")
            print(f"      Power Map: {finding.get('power_map', 'N/A')}")
        elif source == 'v1':
            print(f"\n  {i}. [{source.upper()}] {finding.get('title', 'N/A')}")
            print(f"      {finding.get('message', 'N/A')}")
        else:  # v0
            print(f"\n  {i}. [{source.upper()}] {finding.get('title', 'N/A')}")
            print(f"      {finding.get('message', 'N/A')}")
    
    print(f"\n[Next Actions] ({len(gateway_output.next_actions)} items)")
    for i, action in enumerate(gateway_output.next_actions[:2], 1):  # Show first 2
        print(f"  {i}. {action.get('action', 'N/A')}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Extract text from QQ Music subscription screenshot
    # Based on image description, organized as contract text
    QQ_MUSIC_CONTRACT_TEXT = """
    QQ Music Super Member Monthly Automatic Renewal
    深圳市腾讯计算机系统有限公司
    
    Current Status: 生效中 (In effect)
    Activation Time: 2025-12-12 09:11
    Activated Account: 微信账号 (WeChat Account)
    
    Service Introduction:
    该线上会员服务每月自动续费,扣费金额为20元/月。服务到期当天自动通过微信支付为你发起扣费,自动延长服务有效期。服务关闭后将不再继续扣费。
    
    Deduction Method: 零钱 (Wallet Balance)
    Deduction Record: Available
    
    Close Service: 关闭扣费服务 (Close Deduction Service)
    """
    
    print("Processing QQ Music Subscription Contract...")
    print("=" * 80)
    print("Contract Text:")
    print(QQ_MUSIC_CONTRACT_TEXT)
    
    # Run end-to-end flow
    gateway_output = run_end_to_end(QQ_MUSIC_CONTRACT_TEXT)
    
    # Output first screen (risk assessment)
    output_first_screen(gateway_output)
    
    # Output full Gateway JSON
    gateway_dict = {
        "overview": gateway_output.overview,
        "key_findings": gateway_output.key_findings,
        "next_actions": gateway_output.next_actions,
        "details": gateway_output.details
    }
    
    output_file = "gateway_qqmusic_output.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(gateway_dict, f, ensure_ascii=False, indent=2)
    
    print(f"\nFull Gateway JSON saved to: {output_file}")
    print("=" * 80)

