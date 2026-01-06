"""
FastAPI Web Shell for ClearLease
Minimal HTTP interface to existing ClearLease engine
"""
import sys
import os
import time
import random
from fastapi import FastAPI
from pydantic import BaseModel

# Fix Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from backend.run_gateway_json_output import run_end_to_end

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://clearlease-frontend.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.post("/create-payment-intent")
def create_payment_intent():
    """
    Create a new Stripe PaymentIntent for each request.
    Returns client_secret for frontend use.
    """
    try:
        # Simulate Stripe PaymentIntent creation
        # In a real implementation, this would be:
        # intent = stripe.PaymentIntent.create(
        #     amount=799,  # $7.99 (amount in cents)
        #     currency="usd",
        #     description="ClearLease Premium Analysis",
        # )
        
        # Simulate PaymentIntent response
        timestamp = int(time.time())
        random_id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=14))
        payment_intent_id = f"pi_{random_id}"
        client_secret = f"{payment_intent_id}_secret_{''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=24))}"
        
        # Print PaymentIntent details
        print(f"PaymentIntent.id: {payment_intent_id}")
        print(f"PaymentIntent.client_secret: {client_secret}")
        print(f"PaymentIntent.created: {timestamp}")
        print(f"Amount: 799 (cents)")
        print(f"Currency: usd")
        
        # Return only client_secret to frontend
        return {
            "client_secret": client_secret
        }
    except Exception as e:
        print(f"Error creating PaymentIntent: {e}")
        return {"error": str(e)}


