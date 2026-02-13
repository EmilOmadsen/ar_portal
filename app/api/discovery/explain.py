"""
Explainability API endpoints
Get detailed explanations for track scores
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict

from app.db.session import SessionLocal
from app.core.security import get_current_user
from app.models.discovery import Track, TrackScore

router = APIRouter(
    prefix="/explain",
    tags=["discovery-explain"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{track_id}")
async def explain_track(
    track_id: str,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive explanation for why a track was selected
    
    Returns both trending and evergreen explanations if available
    CRITICAL: Every discovery decision must be explainable
    """
    # Get track
    track = db.query(Track).filter(Track.id == track_id).first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    
    # Get latest scores
    latest_trending = db.query(TrackScore).filter(
        TrackScore.track_id == track_id,
        TrackScore.trending_score.isnot(None)
    ).order_by(TrackScore.computed_at.desc()).first()
    
    latest_evergreen = db.query(TrackScore).filter(
        TrackScore.track_id == track_id,
        TrackScore.evergreen_score.isnot(None)
    ).order_by(TrackScore.computed_at.desc()).first()
    
    result = {
        "track": {
            "id": track.id,
            "title": track.title,
            "artist_name": track.artist_name
        }
    }
    
    # Add trending explanation if available
    if latest_trending:
        result["trending"] = {
            "score": latest_trending.trending_score,
            "computed_at": latest_trending.computed_at.isoformat(),
            "why_selected": latest_trending.why_selected,
            "risk_flags": latest_trending.risk_flags,
            "components": latest_trending.components
        }
    
    # Add evergreen explanation if available
    if latest_evergreen:
        result["evergreen"] = {
            "score": latest_evergreen.evergreen_score,
            "computed_at": latest_evergreen.computed_at.isoformat(),
            "why_selected": latest_evergreen.why_selected,
            "risk_flags": latest_evergreen.risk_flags,
            "components": latest_evergreen.components
        }
    
    if not latest_trending and not latest_evergreen:
        raise HTTPException(
            status_code=404,
            detail="No scores available for this track"
        )
    
    return result


@router.get("/weights/trending")
async def get_trending_weights(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get current trending score weight configuration
    
    Useful for understanding how scores are calculated
    """
    from app.core.discovery.scoring import TRENDING_WEIGHTS, MIN_THRESHOLDS
    
    return {
        "weights": TRENDING_WEIGHTS,
        "thresholds": {
            "min_tiktok_posts_7d": MIN_THRESHOLDS["trending_min_tiktok_posts_7d"],
            "min_spotify_streams_7d": MIN_THRESHOLDS["trending_min_spotify_streams_7d"],
            "min_data_points": MIN_THRESHOLDS["trending_min_data_points"]
        },
        "description": "Trending score focuses on early momentum detection"
    }


@router.get("/weights/evergreen")
async def get_evergreen_weights(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get current evergreen score weight configuration
    """
    from app.core.discovery.scoring import EVERGREEN_WEIGHTS, MIN_THRESHOLDS
    
    return {
        "weights": EVERGREEN_WEIGHTS,
        "thresholds": {
            "min_active_months": MIN_THRESHOLDS["evergreen_min_active_months"],
            "min_data_points": MIN_THRESHOLDS["evergreen_min_data_points"],
            "min_avg_streams": MIN_THRESHOLDS["evergreen_min_avg_streams"]
        },
        "description": "Evergreen score identifies stable, predictable long-term value"
    }
