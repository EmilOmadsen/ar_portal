"""
Pinned Songs Management
Manual override system for trending charts when API data doesn't match external sources
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.db.session import SessionLocal
from app.models.discovery import PinnedSong
from app.core.security import get_current_user

router = APIRouter(
    prefix="/api/discovery/pinned-songs",
    tags=["pinned-songs"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
async def get_pinned_songs(db: Session = Depends(get_db)):
    """Get all active pinned songs in order"""
    pinned = db.query(PinnedSong)\
        .filter(PinnedSong.is_active == True)\
        .order_by(PinnedSong.pin_position)\
        .all()
    
    return [
        {
            "id": p.id,
            "song_name": p.song_name,
            "artist_name": p.artist_name,
            "spotify_id": p.spotify_id,
            "song_image_url": p.song_image_url,
            "label_name": p.label_name,
            "pin_position": p.pin_position,
            "pinned_at": p.pinned_at,
            "notes": p.notes
        }
        for p in pinned
    ]


@router.post("/")
async def add_pinned_song(
    current_user: Dict = Depends(get_current_user),
    song_name: str = Query(...),
    artist_name: str = Query(...),
    pin_position: int = Query(..., ge=1, le=20),
    spotify_id: Optional[str] = Query(None),
    song_image_url: Optional[str] = Query(None),
    label_name: Optional[str] = Query(None),
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Add a song to the pinned chart
    Requires authentication. Position determines order (1=top)
    """
    # Check if position already exists
    existing = db.query(PinnedSong).filter(
        PinnedSong.pin_position == pin_position,
        PinnedSong.is_active == True
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Position {pin_position} already taken by '{existing.song_name}' by {existing.artist_name}"
        )
    
    pinned = PinnedSong(
        song_name=song_name,
        artist_name=artist_name,
        pin_position=pin_position,
        spotify_id=spotify_id,
        song_image_url=song_image_url,
        label_name=label_name,
        pinned_by=current_user.get("sub"),  # User email
        notes=notes
    )
    
    db.add(pinned)
    db.commit()
    db.refresh(pinned)
    
    return {
        "success": True,
        "message": f"Pinned '{song_name}' at position {pin_position}",
        "id": pinned.id
    }


@router.delete("/{pinned_id}")
async def remove_pinned_song(
    pinned_id: int,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a pinned song"""
    pinned = db.query(PinnedSong).filter(PinnedSong.id == pinned_id).first()
    
    if not pinned:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pinned song not found"
        )
    
    # Soft delete - mark as inactive
    pinned.is_active = False
    db.commit()
    
    return {"success": True, "message": "Pinned song removed"}


@router.put("/{pinned_id}")
async def update_pinned_song(
    pinned_id: int,
    current_user: Dict = Depends(get_current_user),
    pin_position: Optional[int] = Query(None, ge=1, le=20),
    notes: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Update pinned song position or notes"""
    pinned = db.query(PinnedSong).filter(PinnedSong.id == pinned_id).first()
    
    if not pinned:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pinned song not found"
        )
    
    if pin_position and pin_position != pinned.pin_position:
        # Check if new position is taken
        existing = db.query(PinnedSong).filter(
            PinnedSong.pin_position == pin_position,
            PinnedSong.is_active == True,
            PinnedSong.id != pinned_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Position {pin_position} already taken"
            )
        
        pinned.pin_position = pin_position
    
    if notes is not None:
        pinned.notes = notes
    
    db.commit()
    
    return {
        "success": True,
        "message": "Pinned song updated",
        "pin_position": pinned.pin_position
    }
