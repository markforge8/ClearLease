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
from typing import Optional
from fastapi import UploadFile, File
from fastapi.responses import StreamingResponse
import io

# Fix Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

# Load environment variables
load_dotenv()

from backend.run_gateway_json_output import run_end_to_end
from backend.database import init_db
from backend.config.database import get_db
from backend.models.data_models import UserProfile, UserProfileResponse, GumroadWebhookPayload, Payment
from backend.utils.password import hash_password, verify_password
from backend.utils.jwt import create_access_token
from backend.utils.auth import get_current_user, get_current_user_optional
import uuid
import json
from datetime import datetime
import time

import os

# Function to save analysis record
def save_analysis_record(user_id: str, analysis_id: str, contract_text: str, basic_result):
    """
    Save analysis record to database.
    Only called when analysis is completed and user is logged in.
    Data source: Analyze API's basic_result (what user is allowed to see)
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Import AnalysisRecord model
        from backend.models.data_models import AnalysisRecord
        
        # Extract data from basic_result (what user is allowed to see)
        overview = basic_result.get('overview', {})
        risk_level = overview.get('risk_level', 'medium')
        summary = overview.get('summary', 'Analysis completed')
        risks = basic_result.get('key_findings', [])
        
        # Create analysis record
        analysis_record = AnalysisRecord(
            analysis_id=analysis_id,
            user_id=user_id,
            original_text=contract_text,
            language="English",  # Default language
            risk_level=risk_level,
            summary=summary,
            risks=json.dumps(risks),
            model_version="v1",
            processing_time=None  # Add if available
        )
        
        # Save to database
        db.add(analysis_record)
        db.commit()
        
        # Log successful save
        print(f"[INFO] History record committed: analysis_id={analysis_id}")
        
    except Exception as e:
        print(f"[ERROR] Error saving analysis record: {str(e)}")

# Get port from environment variable, default to 8080
PORT = int(os.getenv("PORT", "8080"))

from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter

# Create routers
public_auth_router = APIRouter(prefix="/api/auth")
protected_auth_router = APIRouter(prefix="/api/auth")

# ===== MODEL DEFINITIONS =====
# These must come BEFORE route definitions

class AuthResponse(BaseModel):
    success: bool
    data: dict = None
    error: str = None

class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

# ===== ROUTE FUNCTION DEFINITIONS =====
# These must come BEFORE create_app() call

@public_auth_router.post("/register", response_model=AuthResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.
    Performs payment compensation binding check after successful registration.
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
        
        # Perform payment compensation binding check
        # Check if there are existing payment records with paid=true for this email
        existing_payments = db.query(Payment).filter(
            Payment.buyer_email == request.email,
            Payment.paid == True
        ).all()
        
        # Log payment binding process
        print(f"[PAYMENT_BINDING] user={request.email}")
        print(f"[PAYMENT_BINDING] payment_found={len(existing_payments) > 0}")
        
        # If payments exist, update user's paid status
        user_paid_updated = False
        if len(existing_payments) > 0:
            new_user.paid = True
            new_user.paid_at = datetime.utcnow()
            db.commit()
            db.refresh(new_user)
            user_paid_updated = True
            print(f"[PAYMENT_BINDING] user_paid_updated={user_paid_updated}")
        else:
            print(f"[PAYMENT_BINDING] user_paid_updated={user_paid_updated}")
        
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

@public_auth_router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    User login.
    Performs payment compensation binding check after successful login.
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
        
        # Print current user email for debugging
        print("[DEBUG] current user email:", user.email)
        
        # Perform payment compensation binding check
        # Check if there are existing payment records with paid=true for this email
        existing_payments = db.query(Payment).filter(
            Payment.buyer_email == request.email,
            Payment.paid == True
        ).all()
        
        # Log payment binding process
        print(f"[PAYMENT_BINDING] user={request.email}")
        print(f"[PAYMENT_BINDING] payment_found={len(existing_payments) > 0}")
        
        # If payments exist and user is not already marked as paid, update user status
        user_paid_updated = False
        if len(existing_payments) > 0 and not user.paid:
            user.paid = True
            user.paid_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            user_paid_updated = True
            print(f"[PAYMENT_BINDING] user_paid_updated={user_paid_updated}")
        else:
            print(f"[PAYMENT_BINDING] user_paid_updated={user_paid_updated}")
        
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

@protected_auth_router.get("/me", response_model=AuthResponse)
def get_me(current_user: UserProfile = Depends(get_current_user)):
    """
    Get current user information.
    Returns user's paid status from database.
    """
    try:
        # Log that we're retrieving paid status from database
        print(f"[ME ENDPOINT] Retrieving paid status for user: {current_user.email}")
        print(f"[ME ENDPOINT] Current paid status: {current_user.paid}")
        
        # Return user information including paid status
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

@protected_auth_router.post("/logout", response_model=AuthResponse)
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

# ===== END ROUTE FUNCTION DEFINITIONS =====

# Application factory pattern
def create_app():
    """Create and configure the FastAPI application"""
    print("CREATE_APP_CALLED")
    app = FastAPI()
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 开发阶段允许所有域名访问
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Verify router routes before including
    print(f"PUBLIC_AUTH_ROUTES_COUNT: {len(public_auth_router.routes)}")
    print(f"PROTECTED_AUTH_ROUTES_COUNT: {len(protected_auth_router.routes)}")
    
    # Include routers - this happens AFTER all route definitions
    app.include_router(public_auth_router)
    app.include_router(protected_auth_router)
    
    # Verify app routes after including
    print(f"APP_ROUTES_COUNT_AFTER_INCLUDE: {len(app.routes)}")
    
    return app

# Create app instance - this is the entry point for Railway
app = create_app()


@app.on_event("startup")
async def startup_event():
    """
    Initialize the database on application startup.
    """
    init_db()


class AnalyzeRequest(BaseModel):
    contract_text: str





@app.get("/health")
def health():
    return "ok"


@app.post("/analyze")
def analyze(request: AnalyzeRequest, current_user: UserProfile = Depends(get_current_user)):
    """
    Analyze contract text and return分层 results based on user's paid status.
    All users get basic analysis, paid users get full analysis.
    """
    # Add DEBUG log for current_user
    print(f"[DEBUG] analyze current_user = {current_user}")
    
    # Run analysis (always execute regardless of paid status)
    gateway_output = run_end_to_end(request.contract_text)
    
    # Build basic analysis result (for free users)
    basic_result = {
        "overview": gateway_output.overview,
        "key_findings": gateway_output.key_findings,
        "next_actions": gateway_output.next_actions
    }
    
    # Build full analysis result (for paid users)
    full_result = {
        "overview": gateway_output.overview,
        "key_findings": gateway_output.key_findings,
        "next_actions": gateway_output.next_actions,
        "details": gateway_output.details
    }
    
    # Check if user is paid
    is_paid = current_user.paid if current_user else False
    
    # Generate analysis_id for logged-in users
    analysis_id = None
    if current_user:
        analysis_id = str(uuid.uuid4())
        # Log before save
        print(f"[INFO] Before save_analysis_record: analysis_id={analysis_id}")
        # Save analysis record - only save what user is allowed to see (basic_result)
        save_analysis_record(current_user.id, analysis_id, request.contract_text, basic_result)
        # Log after save
        print(f"[INFO] After save_analysis_record: analysis_id={analysis_id}")
    
    # Return response
    return {
        "analysis_id": analysis_id,
        "basic_result": basic_result,
        "full_result": full_result if is_paid else None,
        "locked": not is_paid
    }


@public_auth_router.post("/register", response_model=AuthResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.
    Performs payment compensation binding check after successful registration.
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
        
        # Perform payment compensation binding check
        # Check if there are existing payment records with paid=true for this email
        existing_payments = db.query(Payment).filter(
            Payment.buyer_email == request.email,
            Payment.paid == True
        ).all()
        
        # Log payment binding process
        print(f"[PAYMENT_BINDING] user={request.email}")
        print(f"[PAYMENT_BINDING] payment_found={len(existing_payments) > 0}")
        
        # If payments exist, update user's paid status
        user_paid_updated = False
        if len(existing_payments) > 0:
            new_user.paid = True
            new_user.paid_at = datetime.utcnow()
            db.commit()
            db.refresh(new_user)
            user_paid_updated = True
            print(f"[PAYMENT_BINDING] user_paid_updated={user_paid_updated}")
        else:
            print(f"[PAYMENT_BINDING] user_paid_updated={user_paid_updated}")
        
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


@public_auth_router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    User login.
    Performs payment compensation binding check after successful login.
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
        
        # Print current user email for debugging
        print("[DEBUG] current user email:", user.email)
        
        # Perform payment compensation binding check
        # Check if there are existing payment records with paid=true for this email
        existing_payments = db.query(Payment).filter(
            Payment.buyer_email == request.email,
            Payment.paid == True
        ).all()
        
        # Log payment binding process
        print(f"[PAYMENT_BINDING] user={request.email}")
        print(f"[PAYMENT_BINDING] payment_found={len(existing_payments) > 0}")
        
        # If payments exist and user is not already marked as paid, update user status
        user_paid_updated = False
        if len(existing_payments) > 0 and not user.paid:
            user.paid = True
            user.paid_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            user_paid_updated = True
            print(f"[PAYMENT_BINDING] user_paid_updated={user_paid_updated}")
        else:
            print(f"[PAYMENT_BINDING] user_paid_updated={user_paid_updated}")
        
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


@protected_auth_router.get("/me", response_model=AuthResponse)
def get_me(current_user: UserProfile = Depends(get_current_user)):
    """
    Get current user information.
    Returns user's paid status from database.
    """
    try:
        # Log that we're retrieving paid status from database
        print(f"[ME ENDPOINT] Retrieving paid status for user: {current_user.email}")
        print(f"[ME ENDPOINT] Current paid status: {current_user.paid}")
        
        # Return user information including paid status
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


@protected_auth_router.post("/logout", response_model=AuthResponse)
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


@app.post("/api/dev/reset-paid")
def reset_paid(current_user: UserProfile = Depends(get_current_user)):
    """
    Reset current user's paid status. Only available in development/staging environments.
    """
    try:
        # Check if environment is development or staging
        env = os.getenv("ENVIRONMENT", "development")
        if env not in ["development", "staging"]:
            return {"success": False, "error": "This endpoint is only available in development environments"}
        
        # Get database session
        db = next(get_db())
        
        # Reset user's paid status
        user = db.query(UserProfile).filter(UserProfile.id == current_user.id).first()
        if user:
            user.paid = False
            user.paid_at = None
            user.gumroad_order_id = None
            db.commit()
            print(f"[DEV RESET] Reset paid status for user: {user.email}")
            return {"success": True}
        else:
            return {"success": False, "error": "User not found"}
        
    except Exception as e:
        print(f"Error in reset-paid endpoint: {str(e)}")
        return {"success": False, "error": "Internal server error"}








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


from fastapi import FastAPI, Depends, HTTPException, Header, Request

@app.post("/api/webhook/gumroad")
async def gumroad_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Gumroad webhook events for sales.
    Updates existing user's paid status if user exists.
    Always returns 200 regardless of outcome.
    """
    try:
        # Log webhook hit
        print("[GUMROAD WEBHOOK] Webhook hit")
        
        # Get form data instead of JSON
        form = await request.form()
        print("[GUMROAD WEBHOOK] Received form data:", dict(form))
        
        # Extract all possible email fields from webhook
        email_fields = {
            "email": form.get("email"),
            "purchaser_email": form.get("purchaser_email"),
            "buyer_email": form.get("buyer_email")
        }
        print("[GUMROAD WEBHOOK] All email fields:", email_fields)
        
        # Determine the email to use for user lookup
        # Priority: email > purchaser_email > buyer_email
        user_email = form.get("email") or form.get("purchaser_email") or form.get("buyer_email")
        
        print("[GUMROAD WEBHOOK] Final email used for lookup:", user_email)
        
        # If no email, return 200
        if not user_email:
            print("[GUMROAD WEBHOOK] No email found in form data, returning 200")
            return {"status": "success"}
        
        # Check if user exists with this email
        user = db.query(UserProfile).filter(UserProfile.email == user_email).first()
        
        # Initialize update status
        paid_updated = False
        user_found = user is not None
        
        print("[GUMROAD WEBHOOK] User found in database:", user_found)
        
        # If user not found, print all user emails in database (for development only)
        if not user:
            print("[GUMROAD WEBHOOK] ==== DEVELOPMENT ONLY ====")
            all_users = db.query(UserProfile).all()
            if all_users:
                print("[GUMROAD WEBHOOK] All users in database:")
                for u in all_users:
                    print(f"[GUMROAD WEBHOOK] - {u.email}")
            else:
                print("[GUMROAD WEBHOOK] No users found in database")
            print("[GUMROAD WEBHOOK] ========================")
        
        # Check if this is a test order
        is_test_order = form.get("test") == "true"
        if is_test_order:
            print(f"[GUMROAD WEBHOOK] Test order detected for email: {user_email}")
        
        if user:
            # Update user's paid status to true
            user.paid = True
            user.paid_at = datetime.utcnow()
            # Update gumroad_order_id if provided
            order_id = form.get("order_id")
            if order_id:
                user.gumroad_order_id = order_id
            db.commit()
            paid_updated = True
            print(f"[GUMROAD WEBHOOK] Updated paid status for user: {user_email}")
        else:
            # User doesn't exist, just log
            print(f"[GUMROAD WEBHOOK] User not found for email: {user_email}, skipping paid update")
            paid_updated = False
        
        # Log update status
        print(f"[GUMROAD WEBHOOK] Paid status updated: {paid_updated}")
        
        # Always return 200
        return {"status": "success"}
    except Exception as e:
        # Log any errors
        print(f"[GUMROAD WEBHOOK] Error processing webhook: {e}")
        # Still return 200 to avoid Gumroad retries
        return {"status": "success"}


@app.get("/api/me", response_model=dict)
async def get_user_status(Authorization: str = Header(...), db: Session = Depends(get_db)):
    """
    Get current user's status including paid status.
    Uses Supabase JWT for authentication.
    Returns complete user identity information including id, email, and paid.
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
        
        # Return response in the required format
        return {
            "success": True,
            "data": {
                "id": user.id,
                "email": user.email,
                "paid": user.paid
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in /api/me endpoint: {str(e)}")
        return {
            "success": False,
            "error": "Internal server error"
        }


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


@app.get("/api/debug/routes")
async def debug_routes():
    """
    Debug endpoint to list all registered routes in the running app.
    """
    routes = []
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name
            })
    return {"routes": routes}


@app.get("/history")
def get_history(current_user: UserProfile = Depends(get_current_user)):
    """
    Get current user's recent analysis history.
    Returns the latest 20 analysis records.
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Import AnalysisRecord model
        from backend.models.data_models import AnalysisRecord
        
        # Get recent analysis records for current user
        # Only return records belonging to the current user
        # Order by created_at descending
        # Limit to 20 records (no automatic cleanup)
        recent_records = db.query(AnalysisRecord).filter(
            AnalysisRecord.user_id == current_user.id
        ).order_by(AnalysisRecord.created_at.desc()).limit(20).all()
        
        # Format results
        history = []
        for record in recent_records:
            history.append({
                "analysis_id": record.analysis_id,
                "created_at": record.created_at.isoformat(),
                "risk_level": record.risk_level,
                "summary": record.summary,
                "language": record.language
            })
        
        return {
            "history": history
        }
        
    except Exception as e:
        print(f"Error in history endpoint: {str(e)}")
        return {
            "error": "Failed to retrieve history"
        }


@app.get("/history/{analysis_id}")
def get_history_detail(analysis_id: str, current_user: UserProfile = Depends(get_current_user)):
    """
    Get detailed information for a specific analysis.
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Import AnalysisRecord model
        from backend.models.data_models import AnalysisRecord
        
        # Find the analysis record by ID and user ID
        # Must verify that record belongs to current user
        record = db.query(AnalysisRecord).filter(
            AnalysisRecord.analysis_id == analysis_id,
            AnalysisRecord.user_id == current_user.id
        ).first()
        
        if not record:
            return {
                "error": "Analysis not found"
            }
        
        # Parse risks from JSON string
        import json
        risks = json.loads(record.risks)
        
        # Return detailed information with complete input/output snapshot
        return {
            "analysis_id": record.analysis_id,
            "created_at": record.created_at.isoformat(),
            "input_snapshot": {
                "original_text": record.original_text,
                "language": record.language
            },
            "output_snapshot": {
                "risk_level": record.risk_level,
                "summary": record.summary,
                "risks": risks
            },
            "meta": {
                "model_version": record.model_version,
                "processing_time": record.processing_time
            }
        }
        
    except Exception as e:
        print(f"Error in history detail endpoint: {str(e)}")
        return {
            "error": "Failed to retrieve analysis details"
        }





@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    """
    Upload file and extract text based on file type.
    Supports .txt, .pdf, .png, .jpg, .jpeg files.
    """
    try:
        # Get file extension
        file_ext = file.filename.lower().split('.')[-1]
        
        if file_ext == 'txt':
            # Process text file
            content = await file.read()
            text = content.decode('utf-8', errors='ignore')
            if not text or len(text.strip()) < 10:
                return {"error": "Unable to extract readable text"}
            return {
                "text": text,
                "source_type": "txt"
            }
        
        elif file_ext == 'pdf':
            # Process PDF file
            import pdfplumber
            
            # Save temp file
            temp_path = f"temp_{file.filename}"
            with open(temp_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # Extract text from PDF
            text = ""
            with pdfplumber.open(temp_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            # Clean up temp file
            import os
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            if not text or len(text.strip()) < 10:
                return {"error": "Unable to extract readable text"}
            return {
                "text": text,
                "source_type": "pdf"
            }
        
        elif file_ext in ['png', 'jpg', 'jpeg']:
            # Process image file
            import pytesseract
            from PIL import Image
            import io
            
            # Read image content
            content = await file.read()
            image = Image.open(io.BytesIO(content))
            
            # Extract text using OCR
            text = pytesseract.image_to_string(image, lang='eng')
            
            if not text or len(text) < 200:
                return {"error": "Unable to extract readable text"}
            return {
                "text": text,
                "source_type": "image"
            }
        
        else:
            return {"error": "Unable to extract readable text"}
    
    except Exception as e:
        print(f"Error in ingest endpoint: {str(e)}")
        return {"error": "Unable to extract readable text"}


