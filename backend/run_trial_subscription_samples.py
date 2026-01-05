# run_trial_subscription_samples.py
# Process two trial/subscription samples separately

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
    
    Detects Temporal Lock-in based on:
    - Trial period with automatic subscription start
    - Auto-renewal clauses
    - Continuous subscription mechanisms
    """
    contract_lower = contract_text.lower()
    
    # Detect auto-subscription start after trial
    has_trial_auto_start = any(keyword in contract_lower for keyword in [
        "subscription will start",
        "will start on",
        "自动开始",
        "订阅将开始",
        "trial will",
        "试用期结束后"
    ])
    
    # Detect auto-renewal
    has_auto_renewal = any(keyword in contract_lower for keyword in [
        "automatically renew",
        "automatic renewal",
        "auto renew",
        "continuous",
        "连续",
        "自动续费",
        "自动续约"
    ])
    
    # Detect trial period
    has_trial_period = any(keyword in contract_lower for keyword in [
        "trial",
        "试用",
        "试看",
        "days left",
        "trial period"
    ])
    
    # Determine strength
    if has_trial_auto_start and has_trial_period:
        # Trial -> Auto subscription is HIGH risk (user may forget to cancel)
        strength = Strength.HIGH
    elif has_auto_renewal:
        strength = Strength.HIGH if "continuous" in contract_lower or "连续" in contract_text else Strength.MEDIUM
    else:
        strength = Strength.LOW
    
    # Extract deadline/notice period
    notice_text = ""
    deadline_text = ""
    
    # Try to extract date if mentioned
    import re
    date_patterns = [
        r"(一月|二月|三月|四月|五月|六月|七月|八月|九月|十月|十一月|十二月)\s*(\d+)",
        r"(january|february|march|april|may|june|july|august|september|october|november|december)\s*(\d+)",
        r"(\d+)\s*天",
        r"(\d+)\s*days"
    ]
    
    deadline_found = False
    for pattern in date_patterns:
        match = re.search(pattern, contract_text, re.IGNORECASE)
        if match:
            deadline_text = match.group(0)
            deadline_found = True
            break
    
    if has_trial_auto_start:
        if deadline_found:
            notice_text = f"在试用期结束前（{deadline_text}）取消订阅，否则将自动开始付费"
        else:
            notice_text = "在试用期结束前取消订阅，否则将自动开始付费"
    elif has_auto_renewal:
        notice_text = "在服务到期前关闭自动续费服务"
        if not deadline_found:
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
            "signals": ["AUTO_RENEWAL", "TRIAL_AUTO_START"] if has_trial_auto_start else ["AUTO_RENEWAL"],
            "clause_references": ["试用条款", "订阅条款"] if has_trial_auto_start else ["续费条款"]
        },
        window={
            "exists": True,
            "conditions": notice_text,
            "deadline": deadline_text
        }
    )


def process_sample(sample_name: str, contract_text: str):
    """
    Process a single sample through the full pipeline
    """
    print("\n" + "=" * 80)
    print(f"PROCESSING SAMPLE: {sample_name}")
    print("=" * 80)
    # Skip printing contract text to avoid encoding issues in Windows console
    
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
        doc_id=f"{sample_name.lower().replace(' ', '_')}_sample",
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
        "subscription will start",
        "will start on",
        "自动续费",
        "自动续约",
        "连续",
        "试用",
        "trial"
    ])
    
    if has_temporal_signals:
        try:
            explain_v2_result = explain_service_v2.explain(explain_v2_input)
        except ValueError as e:
            print(f"Explain v2 skipped: {e}")
    
    # 7. Gateway aggregation
    gateway = ExplainGateway()
    gateway_output = gateway.aggregate(
        explain_v0_output=explain_v0_result,
        explain_v1_output=explain_v1_result,
        explain_v2_output=explain_v2_result
    )
    
    return gateway_output


def output_first_screen(sample_name: str, gateway_output):
    """
    Output first screen analysis
    """
    print("\n" + "=" * 80)
    print(f"FIRST SCREEN ANALYSIS - {sample_name}")
    print("=" * 80)
    
    # Key question: Does it have temporal lock-in (trial -> auto subscription)?
    print(f"\n[Risk Level] {gateway_output.overview.get('attention_level', 'N/A').upper()}")
    print(f"[Summary] {gateway_output.overview.get('summary', 'N/A')}")
    
    # Check if v2 detected temporal lock-in
    v2_finding = None
    for finding in gateway_output.key_findings:
        if finding.get('source') == 'v2':
            v2_finding = finding
            break
    
    if v2_finding:
        print(f"\n[Temporal Lock-in Detected] YES")
        print(f"  Mechanism: {v2_finding.get('mechanism', 'N/A')}")
        print(f"  Headline: {v2_finding.get('headline', 'N/A')}")
        print(f"  Core Logic: {v2_finding.get('core_logic', 'N/A')}")
        print(f"  Power Map: {v2_finding.get('power_map', 'N/A')}")
    else:
        print(f"\n[Temporal Lock-in Detected] NO")
    
    print(f"\n[Key Findings] ({len(gateway_output.key_findings)} items)")
    for i, finding in enumerate(gateway_output.key_findings[:3], 1):
        source = finding.get('source', 'unknown')
        if source == 'v2':
            print(f"  {i}. [{source.upper()}] {finding.get('headline', 'N/A')}")
        elif source == 'v1':
            print(f"  {i}. [{source.upper()}] {finding.get('title', 'N/A')}")
        else:
            print(f"  {i}. [{source.upper()}] {finding.get('title', 'N/A')}")
    
    print(f"\n[Next Actions] ({len(gateway_output.next_actions)} items)")
    for i, action in enumerate(gateway_output.next_actions[:2], 1):
        print(f"  {i}. {action.get('action', 'N/A')}")
    
    print("=" * 80)


if __name__ == "__main__":
    # Sample 1: Pro Trial (from first image)
    SAMPLE_1_CONTRACT = """
    Pro Trial - 7 Days Left
    
    Entry-level plan with access to premium models, unlimited Tab completions, and more.
    
    Your subscription will start on 一月 12th.
    
    Start Pro Now
    """
    
    # Sample 2: Bilibili Subscription (from second image)
    SAMPLE_2_CONTRACT = """
    Bilibili Subscription - 包月充电
    
    9分钟试看 (9 minutes trial)
    
    吏贵人专属视频 (Official Noble Exclusive Videos)
    ¥12/月 (¥12/month)
    
    可尊享: 每30日内更新2部精华视频(全网独家深度内容)
    (Enjoy: 2 exclusive high-quality videos updated every 30 days)
    
    连续包月 8.33折 (Continuous monthly subscription 8.33% off)
    立即开通 ¥10 ¥12 (Activate now ¥10 ¥12)
    
    阅读并同意《高档充电计划用户协议》
    (Read and agree to "High-end Charging Plan User Agreement")
    """
    
    # Process Sample 1
    gateway_output_1 = process_sample("Sample 1: Pro Trial", SAMPLE_1_CONTRACT)
    output_first_screen("Sample 1: Pro Trial", gateway_output_1)
    
    # Save JSON for Sample 1
    gateway_dict_1 = {
        "overview": gateway_output_1.overview,
        "key_findings": gateway_output_1.key_findings,
        "next_actions": gateway_output_1.next_actions,
        "details": gateway_output_1.details
    }
    with open("gateway_sample1_pro_trial.json", 'w', encoding='utf-8') as f:
        json.dump(gateway_dict_1, f, ensure_ascii=False, indent=2)
    print(f"\nSample 1 JSON saved to: gateway_sample1_pro_trial.json")
    
    # Process Sample 2
    gateway_output_2 = process_sample("Sample 2: Bilibili Subscription", SAMPLE_2_CONTRACT)
    output_first_screen("Sample 2: Bilibili Subscription", gateway_output_2)
    
    # Save JSON for Sample 2
    gateway_dict_2 = {
        "overview": gateway_output_2.overview,
        "key_findings": gateway_output_2.key_findings,
        "next_actions": gateway_output_2.next_actions,
        "details": gateway_output_2.details
    }
    with open("gateway_sample2_bilibili.json", 'w', encoding='utf-8') as f:
        json.dump(gateway_dict_2, f, ensure_ascii=False, indent=2)
    print(f"\nSample 2 JSON saved to: gateway_sample2_bilibili.json")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY - Temporal Lock-in Detection")
    print("=" * 80)
    print(f"\nSample 1 (Pro Trial):")
    print(f"  Risk Level: {gateway_output_1.overview.get('attention_level', 'N/A').upper()}")
    print(f"  Has Trial -> Auto Subscription: {'YES' if gateway_output_1.overview.get('attention_level') == 'high' else 'NO'}")
    
    print(f"\nSample 2 (Bilibili):")
    print(f"  Risk Level: {gateway_output_2.overview.get('attention_level', 'N/A').upper()}")
    print(f"  Has Continuous Subscription: {'YES' if gateway_output_2.overview.get('attention_level') in ['high', 'medium'] else 'NO'}")
    print("=" * 80)

