"""
FastAPI Web Shell for ClearLease
Minimal HTTP interface to existing ClearLease engine
"""
import sys
import os
import time
import random
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from jose import JWTError, jwt
from dotenv import load_dotenv

# Fix Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

# Load environment variables
load_dotenv()

from backend.run_gateway_json_output import run_end_to_end
from backend.database import init_db
from backend.config.database import get_db
from backend.models.data_models import UserProfile, UserProfileResponse, GumroadWebhookPayload
from backend.utils.password import hash_password, verify_password
from backend.utils.jwt import create_access_token
from backend.utils.auth import get_current_user
from pydantic import BaseModel
import uuid

import os

# Get port from environment variable, default to 8080
PORT = int(os.getenv("PORT", "8080"))

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://clearlease-frontend.vercel.app",
        "http://localhost:3000",  # 开发环境
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """
    Initialize the database on application startup.
    """
    init_db()


class AnalyzeRequest(BaseModel):
    contract_text: str


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    success: bool
    data: dict = None
    error: str = None


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


@app.post("/api/auth/register", response_model=AuthResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    try:
        # Check if email already exists
        existing_user = db.query(UserProfile).filter(UserProfile.email == request.email).first()
        if existing_user:
            return AuthResponse(
                success=False,
                error="Email already exists"
            )
        
        # Hash password
        hashed_password = hash_password(request.password)
        
        # Create new user
        user_id = str(uuid.uuid4())
        new_user = UserProfile(
            id=user_id,
            email=request.email,
            password_hash=hashed_password,
            paid=False,
            paid_at=None,
            gumroad_order_id=None
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Create access token
        access_token = create_access_token(
            data={"sub": new_user.id, "email": new_user.email}
        )
        
        # Return response
        return AuthResponse(
            success=True,
            data={
                "token": access_token,
                "user": {
                    "id": new_user.id,
                    "email": new_user.email,
                    "paid": new_user.paid,
                    "paid_at": new_user.paid_at
                }
            }
        )
        
    except Exception as e:
        print(f"Error in register endpoint: {str(e)}")
        return AuthResponse(
            success=False,
            error="Internal server error"
        )


@app.post("/api/auth/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    User login.
    """
    try:
        # Find user by email
        user = db.query(UserProfile).filter(UserProfile.email == request.email).first()
        if not user:
            return AuthResponse(
                success=False,
                error="Invalid email or password"
            )
        
        # Verify password
        if not verify_password(request.password, user.password_hash):
            return AuthResponse(
                success=False,
                error="Invalid email or password"
            )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email}
        )
        
        # Return response
        return AuthResponse(
            success=True,
            data={
                "token": access_token,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "paid": user.paid,
                    "paid_at": user.paid_at
                }
            }
        )
        
    except Exception as e:
        print(f"Error in login endpoint: {str(e)}")
        return AuthResponse(
            success=False,
            error="Internal server error"
        )


@app.get("/api/auth/me", response_model=AuthResponse)
def get_me(current_user: UserProfile = Depends(get_current_user)):
    """
    Get current user information.
    """
    try:
        # Return user information
        return AuthResponse(
            success=True,
            data={
                "id": current_user.id,
                "email": current_user.email,
                "paid": current_user.paid,
                "paid_at": current_user.paid_at
            }
        )
        
    except Exception as e:
        print(f"Error in get_me endpoint: {str(e)}")
        return AuthResponse(
            success=False,
            error="Internal server error"
        )


@app.post("/api/auth/logout", response_model=AuthResponse)
def logout(current_user: UserProfile = Depends(get_current_user)):
    """
    User logout.
    """
    try:
        # For JWT, logout is primarily handled on the client side
        # by removing the token from storage. This endpoint serves
        # as a confirmation and can be used for any server-side
        # logout logic if needed in the future.
        
        return AuthResponse(
            success=True,
            data={"message": "Logged out successfully"}
        )
        
    except Exception as e:
        print(f"Error in logout endpoint: {str(e)}")
        return AuthResponse(
            success=False,
            error="Internal server error"
        )


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


@app.post("/api/webhook/gumroad")
async def gumroad_webhook(payload: GumroadWebhookPayload, db: Session = Depends(get_db)):
    """
    Handle Gumroad webhook events for sales.
    Updates user's paid status based on the webhook payload.
    """
    try:
        # Extract buyer email and order ID from payload
        buyer_email = payload.buyer_email
        order_id = payload.order_id
        
        print(f"Received Gumroad webhook for email: {buyer_email}, order ID: {order_id}")
        
        # Find user by email in user_profiles
        user = db.query(UserProfile).filter(UserProfile.email == buyer_email).first()
        
        if user:
            # Update user's paid status
            user.paid = True
            user.paid_at = datetime.utcnow()
            user.gumroad_order_id = order_id
            db.commit()
            print(f"Updated user {buyer_email} to paid status")
        else:
            # Log if user not found, but don't error
            print(f"User not found for email: {buyer_email}")
        
        return {"status": "success"}
    except Exception as e:
        print(f"Error processing Gumroad webhook: {e}")
        # Return success even if there's an error to avoid Gumroad retries
        return {"status": "success"}


@app.get("/api/me", response_model=UserProfileResponse)
async def get_user_status(Authorization: str = Header(...), db: Session = Depends(get_db)):
    """
    Get current user's status including paid status.
    Uses Supabase JWT for authentication.
    """
    try:
        # Print received Authorization header
        print(f"Received Authorization header: {Authorization}")
        
        # Extract token from Authorization header
        token = Authorization.replace("Bearer ", "")
        print(f"Extracted token: {token}")
        
        # Verify and decode JWT
        SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
        print(f"JWT secret configured: {SUPABASE_JWT_SECRET is not None}")
        if not SUPABASE_JWT_SECRET:
            raise HTTPException(status_code=500, detail="JWT secret not configured")
        
        try:
            payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
            print(f"Token decoded successfully: {payload}")
        except JWTError as e:
            print(f"JWT decode error: {str(e)}")
            raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")
        
        user_id = payload.get("sub")
        email = payload.get("email")
        print(f"Extracted user_id: {user_id}, email: {email}")
        
        if not user_id or not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Find or create user profile
        user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        
        if not user:
            # Create new user profile if not exists
            user = UserProfile(
                id=user_id,
                email=email,
                paid=False,
                paid_at=None,
                gumroad_order_id=None
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created new user profile for {email}")
        else:
            print(f"Found existing user profile for {email}")
        
        return UserProfileResponse(email=user.email, paid=user.paid)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in /api/me endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/debug/auth")
async def debug_auth(Authorization: str = Header(None)):
    """
    Debug endpoint for authentication issues.
    Returns: whether token was received, decode success, and error reason.
    """
    result = {
        "received_token": False,
        "decode_success": False,
        "error": None,
        "payload": None
    }
    
    if Authorization:
        result["received_token"] = True
        print(f"Debug auth received Authorization: {Authorization}")
        
        try:
            # Extract token from Authorization header
            token = Authorization.replace("Bearer ", "")
            
            # Verify and decode JWT
            SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
            if not SUPABASE_JWT_SECRET:
                result["error"] = "JWT secret not configured"
                return result
            
            payload = jwt.decode(token, SUPABASE_JWT_SECRET, algorithms=["HS256"])
            result["decode_success"] = True
            result["payload"] = {
                "sub": payload.get("sub"),
                "email": payload.get("email"),
                "aud": payload.get("aud"),
                "exp": payload.get("exp")
            }
            print(f"Debug auth decode success: {payload}")
        except JWTError as e:
            result["error"] = f"JWT decode error: {str(e)}"
            print(f"Debug auth JWT error: {str(e)}")
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
            print(f"Debug auth unexpected error: {str(e)}")
    else:
        result["error"] = "No Authorization header provided"
        print("Debug auth: No Authorization header provided")
    
    return result


