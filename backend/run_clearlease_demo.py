# run_clearlease_demo.py
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
    AnalysisOutput,
    ExplainV2Input,
    ExplainV2Output,
    TrapType,
    Strength,
    Beneficiary,
    Irreversibility,
    ConfidenceLevel,
    LockInDynamics
)


def build_explain_v2_input() -> ExplainV2Input:
    """
    Build ExplainV2Input from detected trap (simplified for MVP).
    
    In MVP, we use simplified data to demonstrate the flow.
    In production, this would come from Analysis v2 trap detection.
    """
    return ExplainV2Input(
        trap_type=TrapType.TEMPORAL_LOCK_IN,
        strength=Strength.HIGH,
        beneficiary=Beneficiary.COUNTERPARTY,
        cost_bearer="user",
        irreversibility=Irreversibility.PARTIALLY_REVERSIBLE,
        evidence={
            "signals": ["AUTO_RENEWAL", "SHORT_NOTICE_WINDOW"],
            "clause_references": ["续约条款", "通知条款"]
        },
        window={
            "exists": True,
            "conditions": "在续约窗口关闭前提供书面终止通知",
            "deadline": "合同到期前90天"
        }
    )


def run_demo(contract_text: str):
    print("\n" + "=" * 80)
    print("📄 RAW CONTRACT")
    print("=" * 80)
    print(contract_text)

    # 1. Ingestion
    ingestion_service = IngestionService()
    ingestion_result = ingestion_service.ingest(IngestionInput(text=contract_text))

    # 2. Extraction
    extraction_service = ExtractionService()
    extraction_candidates = extraction_service.extract(ingestion_result.text_blocks)
    # Convert ExtractionCandidate to ExtractedSignal format (simplified)
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
    explain_v2_input = build_explain_v2_input()
    explain_v2_result = explain_service_v2.explain(explain_v2_input)

    # 7. Gateway aggregation
    gateway = ExplainGateway()
    gateway_output = gateway.aggregate(
        explain_v0_output=explain_v0_result,
        explain_v1_output=explain_v1_result,
        explain_v2_output=explain_v2_result
    )

    # -----------------------
    # OUTPUT
    # -----------------------

    print("\n" + "=" * 80)
    print("🧠 V0 ANALYSIS RESULT (Signals / Risk Items)")
    print("=" * 80)
    for item in analysis_output.risk_items:
        print(f"- code={item.risk_code}, severity={item.severity}, rules={item.evidence_rules}")

    print("\n" + "=" * 80)
    print("🧩 V1 STRUCTURAL RISK FIELDS")
    print("=" * 80)

    if not analysis_output.risk_fields:
        print("✅ No structural risk fields detected.")
    else:
        for rf in analysis_output.risk_fields:
            print(
                f"- axis={rf.axis.value}, "
                f"intensity={rf.intensity}, "
                f"affected_party={rf.affected_party}, "
                f"compounding={rf.compounding}, "
                f"blocks={rf.source_blocks}"
            )

    print("\n" + "=" * 80)
    print("🗣️ V1 EXPLANATION (User-facing)")
    print("=" * 80)

    if not explain_v1_result.risk_field_explanations:
        print("✅ No structural risk explanation generated.")
    else:
        for exp in explain_v1_result.risk_field_explanations:
            print(f"\n[{exp.axis.value.upper()} | {exp.intensity.upper()}]")
            print(f"标题: {exp.title}")
            print(f"说明: {exp.message}")
            if exp.user_action:
                print(f"建议: {exp.user_action}")
            if exp.compounding:
                print("⚠️ 该风险与其他条款存在叠加放大效应")

    print("\n" + "=" * 80)
    print("🔗 GATEWAY OUTPUT (Aggregated Explanations)")
    print("=" * 80)
    
    print("\n📊 Overview:")
    print(f"  - v0: {gateway_output.overview.get('v0', {}).get('overall_message', 'N/A')}")
    if 'v1' in gateway_output.overview:
        print(f"  - v1: {gateway_output.overview['v1'].get('risk_field_count', 0)} risk field(s)")
    if 'v2' in gateway_output.overview:
        print(f"  - v2: {gateway_output.overview['v2'].get('headline', 'N/A')}")
    
    print(f"\n🔍 Key Findings: {len(gateway_output.key_findings)} item(s)")
    for i, finding in enumerate(gateway_output.key_findings[:3], 1):  # Show first 3
        print(f"  {i}. [{finding.get('source', 'unknown')}] {finding.get('title', finding.get('headline', 'N/A'))}")
    
    print(f"\n⚡ Next Actions: {len(gateway_output.next_actions)} item(s)")
    for i, action in enumerate(gateway_output.next_actions[:3], 1):  # Show first 3
        print(f"  {i}. [{action.get('source', 'unknown')}] {action.get('action', 'N/A')}")
    
    print(f"\n📋 Details:")
    print(f"  - v0: {len(gateway_output.details.get('v0', {}).get('explanation_blocks', []))} block(s)")
    print(f"  - v1: {len(gateway_output.details.get('v1', {}).get('risk_field_explanations', []))} explanation(s)")
    if 'v2' in gateway_output.details:
        v2_detail = gateway_output.details['v2']
        print(f"  - v2: mechanism={v2_detail.get('mechanism', 'N/A')}, confidence={v2_detail.get('confidence_level', 'N/A')}")

    print("\n" + "=" * 80)
    print("✅ DEMO FINISHED")
    print("=" * 80)


if __name__ == "__main__":
    # ⬇️ 你可以在这里粘贴任何"之前漏掉的条款"
    CONTRACT_TEXT = """
    Tenant accepts the premises in 'as-is' condition.
    Tenant shall be responsible for all HVAC maintenance and any plumbing issues arising during the term,
    regardless of the age of the fixtures.
    Landlord shall not be held liable for any personal injury or property damage caused by structural defects,
    including but not limited to roof leaks or electrical failures.
    """
    
    # Test contract with auto-renewal clause
    TEST_CONTRACT_WITH_AUTO_RENEWAL = """
    This lease shall automatically renew for successive one-year terms unless Tenant provides
    written notice of termination at least 90 days prior to the end of the current term.
    Early termination by Tenant shall result in a penalty equal to the remaining rent due.
    """

    run_demo(CONTRACT_TEXT)
