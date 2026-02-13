from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import msal
import httpx
from typing import Optional, Dict

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_token(token: str) -> Dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Dependency to get current authenticated user from JWT token"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload.get("sub") is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    return payload

# Microsoft Authentication
    
    if payload.get("sub") is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    return payload

# Microsoft Authentication
def get_msal_app():
    """Create MSAL confidential client application"""
    return msal.ConfidentialClientApplication(
        settings.AZURE_CLIENT_ID,
        authority=settings.authority,
        client_credential=settings.AZURE_CLIENT_SECRET,
    )

def get_auth_url(state: str) -> str:
    """Generate Microsoft login URL"""
    msal_app = get_msal_app()
    # Split the scope string into a list of individual scopes
    scopes = settings.AZURE_SCOPE.split()
    auth_url = msal_app.get_authorization_request_url(
        scopes=scopes,
        state=state,
        redirect_uri=settings.AZURE_REDIRECT_URI
    )
    return auth_url

async def get_token_from_code(code: str) -> Optional[Dict]:
    """Exchange authorization code for access token"""
    msal_app = get_msal_app()
    # Split the scope string into a list of individual scopes
    scopes = settings.AZURE_SCOPE.split()
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=scopes,
        redirect_uri=settings.AZURE_REDIRECT_URI
    )
    return result

async def get_user_info(access_token: str) -> Optional[Dict]:
    """Get user information from Microsoft Graph API"""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://graph.microsoft.com/v1.0/me",
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        return None

