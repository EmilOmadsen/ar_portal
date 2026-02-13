from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import httpx
from typing import Optional, Dict, List

from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_current_user

router = APIRouter(
    prefix="/api/mail",
    tags=["mail"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_user_with_token(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """Get user with Microsoft token from database"""
    user = db.query(User).filter(User.email == current_user["sub"]).first()
    
    if not user or not user.microsoft_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No Microsoft token found. Please login with Microsoft."
        )
    
    return user

@router.get("/inbox")
async def get_inbox(
    top: int = 50,
    select: str = "full",
    user: User = Depends(get_user_with_token)
):
    """Get user's inbox messages from Microsoft Graph API
    
    Args:
        top: Number of messages to fetch (default 50)
        select: 'minimal' for list view (id, subject, from, date) or 'full' for all fields
    """
    
    headers = {"Authorization": f"Bearer {user.microsoft_token}"}
    
    # Optimize query based on select parameter
    if select == "minimal":
        # Fast list view - only essential fields
        query_params = (
            f"$select=id,conversationId,subject,from,receivedDateTime,isRead,hasAttachments"
            f"&$orderby=receivedDateTime desc"
            f"&$top={top}"
        )
    else:
        # Full view with body preview and attachments
        query_params = f"$top={top}&$orderby=receivedDateTime desc&$expand=attachments"
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.get(
            f"https://graph.microsoft.com/v1.0/me/messages?{query_params}",
            headers=headers
        )
        
        if response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Microsoft token expired. Please login again."
            )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch emails: {response.text}"
            )
        
        data = response.json()
        return data

@router.get("/sent")
async def get_sent(
    top: int = 50,
    select: str = "full",
    user: User = Depends(get_user_with_token)
):
    """Get user's sent messages from Microsoft Graph API
    
    Args:
        top: Number of messages to fetch (default 50)
        select: 'minimal' for list view or 'full' for all fields
    """
    
    headers = {"Authorization": f"Bearer {user.microsoft_token}"}
    
    # Optimize query based on select parameter
    if select == "minimal":
        query_params = (
            f"$select=id,conversationId,subject,toRecipients,sentDateTime,hasAttachments"
            f"&$orderby=sentDateTime desc"
            f"&$top={top}"
        )
    else:
        query_params = f"$top={top}&$orderby=sentDateTime desc"
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.get(
            f"https://graph.microsoft.com/v1.0/me/mailFolders/SentItems/messages?{query_params}",
            headers=headers
        )
        
        if response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Microsoft token expired. Please login again."
            )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch sent emails: {response.text}"
            )
        
        data = response.json()
        return data

@router.get("/message/{message_id}")
async def get_message(
    message_id: str,
    user: User = Depends(get_user_with_token)
):
    """Get a specific message with attachments"""
    
    headers = {"Authorization": f"Bearer {user.microsoft_token}"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"https://graph.microsoft.com/v1.0/me/messages/{message_id}?$expand=attachments",
            headers=headers
        )
        
        if response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Microsoft token expired. Please login again."
            )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch message: {response.text}"
            )
        
        return response.json()

@router.get("/conversation/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user: User = Depends(get_user_with_token)
):
    """Get all messages in a conversation thread"""
    
    headers = {"Authorization": f"Bearer {user.microsoft_token}"}
    
    print(f"Fetching conversation: {conversation_id}")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://graph.microsoft.com/v1.0/me/messages?$filter=conversationId eq '{conversation_id}'&$orderby=receivedDateTime asc",
            headers=headers
        )
        
        print(f"Graph API response status: {response.status_code}")
        print(f"Graph API response: {response.text[:500]}")
        
        if response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Microsoft token expired. Please login again."
            )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch conversation: {response.text}"
            )
        
        data = response.json()
        return data

@router.get("/folders")
async def get_folders(user: User = Depends(get_user_with_token)):
    """Get user's mail folders"""
    
    headers = {"Authorization": f"Bearer {user.microsoft_token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://graph.microsoft.com/v1.0/me/mailFolders?$top=100",
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch folders"
            )
        
        return response.json()

@router.get("/folder/{folder_id}/messages")
async def get_folder_messages(
    folder_id: str,
    top: int = 50,
    select: str = "minimal",
    user: User = Depends(get_user_with_token)
):
    """Get messages from a specific folder by ID"""
    
    headers = {"Authorization": f"Bearer {user.microsoft_token}"}
    
    # Optimize query based on select parameter
    if select == "minimal":
        query_params = (
            f"$select=id,conversationId,subject,from,receivedDateTime,isRead,hasAttachments"
            f"&$orderby=receivedDateTime desc"
            f"&$top={top}"
        )
    else:
        query_params = f"$top={top}&$orderby=receivedDateTime desc&$expand=attachments"
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.get(
            f"https://graph.microsoft.com/v1.0/me/mailFolders/{folder_id}/messages?{query_params}",
            headers=headers
        )
        
        if response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Microsoft token expired. Please login again."
            )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to fetch folder messages: {response.text}"
            )
        
        return response.json()

@router.post("/send")
async def send_mail(
    message: Dict,
    user: User = Depends(get_user_with_token)
):
    """Send an email via Microsoft Graph API"""
    
    headers = {
        "Authorization": f"Bearer {user.microsoft_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": message,
        "saveToSentItems": "true"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://graph.microsoft.com/v1.0/me/sendMail",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 401:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Microsoft token expired. Please login again."
            )
        
        if response.status_code not in [200, 202]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send email: {response.text}"
            )
        
        return {"status": "sent", "message": "Email sent successfully"}

@router.get("/message/{message_id}")
async def get_message(
    message_id: str,
    user: User = Depends(get_user_with_token)
):
    """Get a specific message by ID"""
    
    headers = {"Authorization": f"Bearer {user.microsoft_token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://graph.microsoft.com/v1.0/me/messages/{message_id}",
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        return response.json()
