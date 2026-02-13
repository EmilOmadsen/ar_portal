"""
Evergreen tracks API endpoints
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Dict
from datetime import datetime

from app.db.session import SessionLocal
from app.core.security import get_current_user
from app.core.discovery.selectors import EvergreenSelector
from app.models.discovery import Track, TrackScore

router = APIRouter(
    prefix="/evergreen",
    tags=["discovery-evergreen"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
async def get_evergreen_tracks(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200, description="Max tracks to return"),
    min_score: float = Query(60.0, ge=0, le=100, description="Minimum evergreen score"),
    min_months: int = Query(6, ge=3, le=24, description="Minimum months of history")
):
    """
    Get evergreen tracks with scores and explanations
    
    Evergreen = stable, predictable long-term value
    NOT viral, NOT trending
    
    Returns tracks sorted by evergreen score (high to low)
    Each track includes:
    - Evergreen score (0-100)
    - Component scores breakdown
    - Human-readable explanation
    - Risk flags
    """
    try:
        tracks = EvergreenSelector.select_tracks(
            db=db,
            limit=limit,
            min_score=min_score,
            min_months=min_months
        )
        
        return {
            "total": len(tracks),
            "limit": limit,
            "min_score": min_score,
            "min_months": min_months,
            "tracks": tracks
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching evergreen tracks: {str(e)}")


@router.get("/{track_id}")
async def get_evergreen_track_details(
    track_id: str,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed evergreen analysis for a specific track
    """
    # Get track
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Get latest score
    latest_score = db.query(TrackScore).filter(
        TrackScore.track_id == track_id,
        TrackScore.evergreen_score.isnot(None)
    ).order_by(TrackScore.computed_at.desc()).first()
    
    if not latest_score:
        raise HTTPException(status_code=404, detail="No evergreen score available for this track")
    
    # Get historical scores
    historical_scores = db.query(TrackScore).filter(
        TrackScore.track_id == track_id,
        TrackScore.evergreen_score.isnot(None)
    ).order_by(TrackScore.computed_at.desc()).limit(30).all()
    
    return {
        "track": {
            "id": track.id,
            "title": track.title,
            "artist_name": track.artist_name,
            "spotify_id": track.spotify_id,
            "isrc": track.isrc,
            "first_discovered": track.first_discovered.isoformat(),
            "last_updated": track.last_updated.isoformat()
        },
        "current_score": {
            "evergreen_score": latest_score.evergreen_score,
            "computed_at": latest_score.computed_at.isoformat(),
            "components": latest_score.components,
            "why_selected": latest_score.why_selected,
            "risk_flags": latest_score.risk_flags
        },
        "history": [
            {
                "score": score.evergreen_score,
                "computed_at": score.computed_at.isoformat()
            }
            for score in historical_scores
        ]
    }


@router.post("/refresh/{track_id}")
async def refresh_evergreen_score(
    track_id: str,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger evergreen score recalculation for a track
    """
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Calculate and persist new score
    track_score = EvergreenSelector.score_and_persist(track, track_id, db)
    
    if not track_score:
        raise HTTPException(
            status_code=400,
            detail="Track does not meet minimum thresholds for evergreen scoring"
        )
    
    return {
        "track_id": track_id,
        "evergreen_score": track_score.evergreen_score,
        "computed_at": track_score.computed_at.isoformat(),
        "why_selected": track_score.why_selected,
        "risk_flags": track_score.risk_flags
    }
