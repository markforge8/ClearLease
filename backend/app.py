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

# Fix Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

# Load environment variables
load_dotenv()

from backend.run_gateway_json_output import run_end_to_end
from backend.database import init_db
from backend.config.database import get_db
from backend.models.data_models import UserProfile, UserProfileResponse, GumroadWebhookPayload, AnalysisDraft, AnalysisDraftResponse, Payment
from backend.utils.password import hash_password, verify_password
from backend.utils.jwt import create_access_token
from backend.utils.auth import get_current_user, get_current_user_optional
import uuid
import json
from datetime import datetime

import os

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
        allow_origins=[
            "https://clearlease-frontend.vercel.app",
            "https://clearlease-frontend-ce76hevcm-mark-forges-projects.vercel.app",  # 前端部署域名
            "http://localhost:3000",  # 开发环境
            "https://clearlease-production.up.railway.app"  # Railway 公网域名
        ],
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
def analyze(request: AnalyzeRequest, current_user: Optional[UserProfile] = Depends(get_current_user_optional)):
    """
    Analyze contract text and return分层 results based on user's paid status.
    All users get basic analysis, paid users get full analysis.
    """
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
    
    # Generate analysis_id and save draft for logged-in users
    analysis_id = None
    if current_user:
        analysis_id = str(uuid.uuid4())
        # Create analysis draft
        analysis_draft = AnalysisDraft(
            id=analysis_id,
            user_id=current_user.id,
            contract_text=request.contract_text,
            preview=json.dumps(basic_result),
            full_analysis=json.dumps(full_result),
            locked=True,
            created_at=datetime.utcnow(),
            unlocked_at=None
        )
        # Save to database
        db = next(get_db())
        db.add(analysis_draft)
        db.commit()
        db.refresh(analysis_draft)
        
        # If user is paid, unlock the analysis
        if is_paid:
            analysis_draft.locked = False
            analysis_draft.unlocked_at = datetime.utcnow()
            db.commit()
            db.refresh(analysis_draft)
    
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


@app.get("/api/analysis/current")
def get_current_analysis(current_user: UserProfile = Depends(get_current_user)):
    """
    Get the current user's latest analysis draft.
    If user is paid, unlock and return full analysis.
    """
    try:
        # Get database session
        db = next(get_db())
        
        # Find the latest locked analysis draft for this user
        latest_draft = db.query(AnalysisDraft).filter(
            AnalysisDraft.user_id == current_user.id,
            AnalysisDraft.locked == True
        ).order_by(
            AnalysisDraft.created_at.desc()
        ).first()
        
        # If no draft found, return error
        if not latest_draft:
            return {
                "success": False,
                "error": "No analysis draft found"
            }
        
        # Check if user is paid
        is_paid = current_user.paid
        
        # Parse preview and full analysis from JSON strings
        preview = json.loads(latest_draft.preview)
        full_analysis = json.loads(latest_draft.full_analysis) if latest_draft.full_analysis else None
        
        # If user is paid, unlock the analysis
        if is_paid:
            latest_draft.locked = False
            latest_draft.unlocked_at = datetime.utcnow()
            db.commit()
            db.refresh(latest_draft)
        
        # Return response
        return {
            "success": True,
            "data": {
                "analysis_id": latest_draft.id,
                "preview": preview,
                "full_analysis": full_analysis if is_paid else None,
                "locked": not is_paid
            }
        }
        
    except Exception as e:
        print(f"Error in get_current_analysis endpoint: {str(e)}")
        return {
            "success": False,
            "error": "Internal server error"
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


