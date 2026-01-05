# run_clearlease_batch_demo.py

import sys
import os

# -----------------------------
# Fix Python path (DO NOT TOUCH)
# -----------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

# -----------------------------
# Imports (fixed, stable)
# -----------------------------
from backend.layers.ingestion.ingestion_service import IngestionService
from backend.layers.extraction.extraction_service import ExtractionService
from backend.layers.analysis.analysis_service import AnalysisService
from backend.layers.explain.explain_v1_service import ExplainV1Service
from backend.models.data_models import IngestionInput, ExtractedSignal


# -----------------------------
# Wrapper functions for pipeline
# -----------------------------
def ingestion_service_ingest(contract_text: str):
    """Wrapper for ingestion service."""
    service = IngestionService()
    input_data = IngestionInput(text=contract_text)
    return service.ingest(input_data)


def extraction_service_extract_signals(ingestion_result):
    """Wrapper for extraction service, converts ExtractionCandidate to ExtractedSignal."""
    service = ExtractionService()
    candidates = service.extract(ingestion_result.text_blocks)
    
    # Convert ExtractionCandidate to ExtractedSignal
    signals = []
    for idx, candidate in enumerate(candidates):
        signal = ExtractedSignal(
            rule_id=candidate.rule_id,
            type=candidate.rule_type,
            hit_text=candidate.extracted_text,
            block_id=candidate.block_id,
            order=idx
        )
        signals.append(signal)
    return signals


def analyze(ingestion_result, extraction_result):
    """Wrapper for analysis service, converts AnalysisOutput to dict."""
    from backend.models.data_models import AnalysisInput
    
    service = AnalysisService()
    analysis_input = AnalysisInput(
        doc_id="demo_doc",
        extracted_signals=extraction_result
    )
    
    analysis_output = service.analyze(analysis_input)
    
    # Convert to dict format
    return {
        "risk_fields": analysis_output.risk_fields,
        "risk_items": analysis_output.risk_items
    }


def explain_v1(risk_fields):
    """Wrapper for explain v1 service."""
    service = ExplainV1Service()
    return service.explain(risk_fields)


# -----------------------------
# Test Contracts (COPY HERE)
# -----------------------------
TEST_CONTRACTS = {
    "A_full_transfer_and_disclaimer": """
Tenant accepts the premises in 'as-is' condition.
Tenant shall be responsible for all HVAC maintenance and any plumbing issues arising during the term,
regardless of the age or condition of the fixtures.
Landlord shall not be held liable for any personal injury or property damage caused by structural defects,
including but not limited to roof leaks or electrical failures.
""",

    "B_auto_renewal_and_penalty": """
This lease shall automatically renew for successive one-year terms unless Tenant provides
written notice of termination at least 90 days prior to the end of the current term.
Early termination by Tenant shall result in a penalty equal to the remaining rent due
for the full lease term.
""",

    "C_liability_only": """
Landlord shall not be responsible for any loss or damage to Tenant's personal property,
except in cases of gross negligence.
Tenant shall notify Landlord promptly of any structural issues.
""",

    "D_clean_contract": """
Landlord shall be responsible for all structural repairs, including roofing, plumbing,
and electrical systems.
Tenant may terminate this lease with 30 days written notice without penalty.
""",

    "E_compounded_risk_trap": """
Tenant accepts the premises in 'as-is' condition.
This lease shall automatically renew unless terminated by Landlord.
Tenant shall be responsible for all maintenance and repairs during the term.
Landlord shall not be liable for damages arising from any defects, known or unknown.
"""
}


# -----------------------------
# Pipeline Runner (DO NOT TOUCH)
# -----------------------------
def run_pipeline(contract_text: str):
    ingestion_result = ingestion_service_ingest(contract_text)
    extraction_result = extraction_service_extract_signals(ingestion_result)

    analysis_result = analyze(
        ingestion_result=ingestion_result,
        extraction_result=extraction_result
    )

    explain_v1_result = explain_v1(analysis_result["risk_fields"])

    return {
        "risk_fields": analysis_result["risk_fields"],
        "explain_v1": explain_v1_result.risk_field_explanations
    }


# -----------------------------
# Batch Runner
# -----------------------------
def run_batch():
    for name, text in TEST_CONTRACTS.items():
        print("\n" + "=" * 30)
        print(f"TEST CASE: {name}")
        print("=" * 30)

        result = run_pipeline(text)

        print("\nRisk Fields:")
        if not result["risk_fields"]:
            print("  [OK] No structural risk detected.")
        else:
            for rf in result["risk_fields"]:
                print(
                    f"  - axis={rf.axis.value}, "
                    f"intensity={rf.intensity}, "
                    f"affected_party={rf.affected_party}"
                )

        print("\nExplain v1:")
        if not result["explain_v1"]:
            print("  [OK] No explanation generated.")
        else:
            for exp in result["explain_v1"]:
                print(f"  - {exp.title}")
                print(f"    {exp.message}")
                if exp.user_action:
                    print(f"    -> {exp.user_action}")


# -----------------------------
# Entry
# -----------------------------
if __name__ == "__main__":
    run_batch()
