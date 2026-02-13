from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
import secrets

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import (
    verify_password, 
    create_access_token, 
    get_auth_url,
    get_token_from_code,
    get_user_info
)

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Store states temporarily (in production, use Redis or database)
oauth_states = {}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/login")
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    token = create_access_token({
        "sub": user.email,
        "role": user.role
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }

@router.get("/microsoft/login")
async def microsoft_login():
    """Initiate Microsoft OAuth login flow"""
    print("=== Microsoft Login Initiated ===")
    
    # Generate a random state for CSRF protection
    state = secrets.token_urlsafe(32)
    oauth_states[state] = True  # Store state temporarily
    
    # Get Microsoft login URL
    auth_url = get_auth_url(state)
    
    print(f"Auth URL: {auth_url}")
    print(f"State: {state}")
    
    return {"auth_url": auth_url}

@router.get("/microsoft/callback")
async def microsoft_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
    error_description: str = None
):
    """Handle Microsoft OAuth callback"""
    print(f"=== Microsoft Callback Called ===")
    print(f"Full URL: {request.url}")
    print(f"Code: {code}")
    print(f"State: {state}")
    print(f"Error: {error}")
    print(f"Error Description: {error_description}")
    
    # Get DB session inside function to avoid dependency errors
    db = SessionLocal()
    
    # Check if Microsoft returned an error
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Microsoft auth error: {error} - {error_description}"
        )
    
    if not code or not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing code or state parameter"
        )
    
    # Verify state to prevent CSRF attacks
    if state not in oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )
    
    # Remove used state
    oauth_states.pop(state, None)
    
    # Exchange code for token
    token_result = await get_token_from_code(code)
    
    if "error" in token_result:
        # Log detailed error for debugging
        error_desc = token_result.get('error_description', 'Unknown error')
        error_code = token_result.get('error', 'unknown')
        print(f"MSAL Error: {error_code} - {error_desc}")
        print(f"Full error: {token_result}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {error_code} - {error_desc}"
        )
    
    access_token = token_result.get("access_token")
    
    # Get user info from Microsoft Graph
    user_info = await get_user_info(access_token)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to get user information"
        )
    
    email = user_info.get("mail") or user_info.get("userPrincipalName")
    display_name = user_info.get("displayName")
    
    # Check if user exists in database
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Create new user
        user = User(
            email=email,
            name=display_name,
            role="user",
            microsoft_token=access_token,
            microsoft_refresh_token=token_result.get("refresh_token")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update existing user's Microsoft tokens
        user.microsoft_token = access_token
        user.microsoft_refresh_token = token_result.get("refresh_token")
        db.commit()
    
    # Create JWT token for your application
    app_token = create_access_token({
        "sub": user.email,
        "role": user.role,
        "name": display_name
    })
    
    # Redirect to dashboard with user info
    from urllib.parse import urlencode
    params = urlencode({
        "token": app_token,
        "name": display_name,
        "email": email,
        "role": user.role
    })
    
    db.close()
    
    return RedirectResponse(url=f"/dashboard?{params}")

@router.get("/logout")
async def logout():
    """
    Logout endpoint that redirects to Microsoft logout page.
    This allows the user to sign out completely from their Microsoft account
    and enables switching to a different account.
    """
    from app.core.config import settings
    
    # Microsoft logout URL that will clear the session and allow account switching
    # The post_logout_redirect_uri takes the user back to our login page
    logout_url = (
        f"{settings.authority}/oauth2/v2.0/logout?"
        f"post_logout_redirect_uri=http://localhost:8000/"
    )
    
    return RedirectResponse(url=logout_url)
