"""
A&R shortlists management API
Human curation and workflow tracking
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Optional, List
from pydantic import BaseModel

from app.db.session import SessionLocal
from app.core.security import get_current_user
from app.models.discovery import Shortlist, Track
from app.models.user import User

router = APIRouter(
    prefix="/shortlist",
    tags=["discovery-shortlist"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class AddToShortlistRequest(BaseModel):
    track_id: str
    priority: int = 0  # 0=normal, 1=high, 2=urgent
    notes: Optional[str] = None


class UpdateShortlistRequest(BaseModel):
    status: Optional[str] = None  # new, contacted, interested, passed, signed
    priority: Optional[int] = None
    notes: Optional[str] = None


@router.get("/")
async def get_shortlist(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    status: Optional[str] = None
):
    """
    Get A&R shortlist with optional status filter
    
    Statuses:
    - new: Just added
    - contacted: Outreach initiated
    - interested: Artist responded positively
    - passed: Not pursuing
    - signed: Deal closed
    """
    # Get user
    user = db.query(User).filter(User.email == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Build query
    query = db.query(Shortlist).filter(Shortlist.user_id == user.id)
    
    if status:
        query = query.filter(Shortlist.status == status)
    
    # Get results with track info
    shortlist_items = query.order_by(
        Shortlist.priority.desc(),
        Shortlist.added_at.desc()
    ).all()
    
    results = []
    for item in shortlist_items:
        track = db.query(Track).filter(Track.id == item.track_id).first()
        if track:
            results.append({
                "id": item.id,
                "track": {
                    "id": track.id,
                    "title": track.title,
                    "artist_name": track.artist_name
                },
                "status": item.status,
                "priority": item.priority,
                "notes": item.notes,
                "added_at": item.added_at.isoformat(),
                "contacted_at": item.contacted_at.isoformat() if item.contacted_at else None,
                "last_updated": item.last_updated.isoformat()
            })
    
    return {
        "total": len(results),
        "status_filter": status,
        "items": results
    }


@router.post("/")
async def add_to_shortlist(
    request: AddToShortlistRequest,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add track to A&R shortlist
    """
    # Get user
    user = db.query(User).filter(User.email == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if track exists
    track = db.query(Track).filter(Track.id == request.track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Check if already in shortlist
    existing = db.query(Shortlist).filter(
        Shortlist.track_id == request.track_id,
        Shortlist.user_id == user.id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Track already in shortlist")
    
    # Create shortlist entry
    shortlist_item = Shortlist(
        track_id=request.track_id,
        user_id=user.id,
        priority=request.priority,
        notes=request.notes,
        status="new"
    )
    
    db.add(shortlist_item)
    db.commit()
    db.refresh(shortlist_item)
    
    return {
        "id": shortlist_item.id,
        "track_id": request.track_id,
        "status": shortlist_item.status,
        "priority": shortlist_item.priority,
        "added_at": shortlist_item.added_at.isoformat()
    }


@router.patch("/{shortlist_id}")
async def update_shortlist_item(
    shortlist_id: int,
    request: UpdateShortlistRequest,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update shortlist item status, priority, or notes
    """
    # Get user
    user = db.query(User).filter(User.email == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get shortlist item
    item = db.query(Shortlist).filter(
        Shortlist.id == shortlist_id,
        Shortlist.user_id == user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Shortlist item not found")
    
    # Update fields
    if request.status is not None:
        valid_statuses = ["new", "contacted", "interested", "passed", "signed"]
        if request.status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
        item.status = request.status
        
        # Set contacted_at if moving to contacted status
        if request.status == "contacted" and item.contacted_at is None:
            from datetime import datetime
            item.contacted_at = datetime.utcnow()
    
    if request.priority is not None:
        item.priority = request.priority
    
    if request.notes is not None:
        item.notes = request.notes
    
    db.commit()
    db.refresh(item)
    
    return {
        "id": item.id,
        "track_id": item.track_id,
        "status": item.status,
        "priority": item.priority,
        "notes": item.notes,
        "last_updated": item.last_updated.isoformat()
    }


@router.delete("/{shortlist_id}")
async def remove_from_shortlist(
    shortlist_id: int,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove track from shortlist
    """
    # Get user
    user = db.query(User).filter(User.email == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get shortlist item
    item = db.query(Shortlist).filter(
        Shortlist.id == shortlist_id,
        Shortlist.user_id == user.id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Shortlist item not found")
    
    db.delete(item)
    db.commit()
    
    return {"message": "Removed from shortlist", "id": shortlist_id}
