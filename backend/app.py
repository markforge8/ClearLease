"""
FastAPI Web Shell for ClearLease
Minimal HTTP interface to existing ClearLease engine
"""
import sys
import os
from fastapi import FastAPI
from pydantic import BaseModel

# Fix Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from backend.run_gateway_json_output import run_end_to_end

app = FastAPI()


class AnalyzeRequest(BaseModel):
    contract_text: str


@app.get("/health")
def health():
    return "ok"


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    gateway_output = run_end_to_end(request.contract_text)
    return {
        "overview": gateway_output.overview,
        "key_findings": gateway_output.key_findings,
        "next_actions": gateway_output.next_actions,
        "details": gateway_output.details
    }

