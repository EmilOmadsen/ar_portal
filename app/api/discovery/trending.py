"""
Trending tracks API endpoints
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, Dict, List
from datetime import datetime

from app.db.session import SessionLocal
from app.core.security import get_current_user
from app.core.discovery.selectors import TrendingSelector
from app.models.discovery import Track, TrackScore

router = APIRouter(
    prefix="/trending",
    tags=["discovery-trending"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
async def get_trending_tracks(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200, description="Max tracks to return"),
    min_score: float = Query(50.0, ge=0, le=100, description="Minimum trending score"),
    platform: Optional[str] = Query(None, description="Filter by platform: spotify, tiktok"),
    country: Optional[str] = Query(None, description="Filter by country code (e.g., DK)")
):
    """
    Get trending tracks with scores and explanations
    
    Returns tracks sorted by trending score (high to low)
    Each track includes:
    - Trending score (0-100)
    - Component scores breakdown
    - Human-readable explanation (why_selected)
    - Risk flags
    """
    try:
        tracks = TrendingSelector.select_tracks(
            db=db,
            limit=limit,
            min_score=min_score,
            platform=platform,
            country=country
        )
        
        return {
            "total": len(tracks),
            "limit": limit,
            "min_score": min_score,
            "filters": {
                "platform": platform,
                "country": country
            },
            "tracks": tracks
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching trending tracks: {str(e)}")


@router.get("/{track_id}")
async def get_trending_track_details(
    track_id: str,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed trending analysis for a specific track
    
    Returns full score breakdown, historical scores, and explanation
    """
    # Get track
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Get latest score
    latest_score = db.query(TrackScore).filter(
        TrackScore.track_id == track_id,
        TrackScore.trending_score.isnot(None)
    ).order_by(TrackScore.computed_at.desc()).first()
    
    if not latest_score:
        raise HTTPException(status_code=404, detail="No trending score available for this track")
    
    # Get historical scores
    historical_scores = db.query(TrackScore).filter(
        TrackScore.track_id == track_id,
        TrackScore.trending_score.isnot(None)
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
            "trending_score": latest_score.trending_score,
            "computed_at": latest_score.computed_at.isoformat(),
            "components": latest_score.components,
            "why_selected": latest_score.why_selected,
            "risk_flags": latest_score.risk_flags
        },
        "history": [
            {
                "score": score.trending_score,
                "computed_at": score.computed_at.isoformat()
            }
            for score in historical_scores
        ]
    }


@router.post("/refresh/{track_id}")
async def refresh_trending_score(
    track_id: str,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger trending score recalculation for a track
    
    Useful for:
    - Testing
    - On-demand updates
    - After manual data corrections
    """
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Calculate and persist new score
    track_score = TrendingSelector.score_and_persist(track, track_id, db)
    
    if not track_score:
        raise HTTPException(
            status_code=400,
            detail="Track does not meet minimum thresholds for trending scoring"
        )
    
    return {
        "track_id": track_id,
        "trending_score": track_score.trending_score,
        "computed_at": track_score.computed_at.isoformat(),
        "why_selected": track_score.why_selected,
        "risk_flags": track_score.risk_flags
    }
