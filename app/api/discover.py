from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
from datetime import datetime

from app.db.session import SessionLocal
from app.core.security import get_current_user
from app.models.discovery import Track, TrackMetric
from sqlalchemy import func

router = APIRouter(
    prefix="/api/discover",
    tags=["discover"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/songs")
async def get_trending_songs(
    response: Response,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    filter_type: Optional[str] = None,
    view: Optional[str] = Query("trending", description="View type: trending or evergreen")
):
    """
    Get trending or evergreen songs
    
    Parameters:
    - limit: Number of songs to return (1-100)
    - offset: Pagination offset
    - filter_type: Optional filter (e.g., 'viral', 'rising', 'new')
    - view: 'trending' for cross-platform trending, 'evergreen' for consistent performers
    """
    
    # Set cache control headers to prevent browser caching
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    # Get all tracks with metrics
    tracks_query = db.query(Track).all()
    
    songs = []
    for track in tracks_query:
        # Get latest metrics
        latest_metric = db.query(TrackMetric).filter(
            TrackMetric.track_id == track.id
        ).order_by(TrackMetric.timestamp.desc()).first()
        
        if not latest_metric:
            continue
        
        # Get historical metrics for evergreen calculation
        all_metrics = db.query(TrackMetric).filter(
            TrackMetric.track_id == track.id
        ).order_by(TrackMetric.timestamp.desc()).limit(30).all()
        
        # Calculate cross-platform score
        tiktok_posts = latest_metric.tiktok_posts or 0
        spotify_streams = latest_metric.spotify_streams or 0
        
        # TRENDING VIEW: Prioritize cross-platform confirmation
        if view == "trending":
            # Base scores
            tiktok_score = 0
            spotify_score = 0
            cross_platform_bonus = 0
            
            # TikTok scoring
            if tiktok_posts > 5000000:
                tiktok_score = 50
            elif tiktok_posts > 2000000:
                tiktok_score = 40
            elif tiktok_posts > 1000000:
                tiktok_score = 30
            elif tiktok_posts > 500000:
                tiktok_score = 20
            
            # Spotify scoring
            if spotify_streams > 50000000:
                spotify_score = 40
            elif spotify_streams > 10000000:
                spotify_score = 30
            elif spotify_streams > 1000000:
                spotify_score = 20
            elif spotify_streams > 100000:
                spotify_score = 10
            
            # Cross-platform confirmation bonus (TikTok virality → Spotify streams)
            if tiktok_posts > 1000000 and spotify_streams > 1000000:
                cross_platform_bonus = 30  # HUGE bonus for both platforms
            elif tiktok_posts > 500000 and spotify_streams > 100000:
                cross_platform_bonus = 20
            elif tiktok_posts > 0 and spotify_streams > 0:
                cross_platform_bonus = 10
            
            trend_score = min(100, tiktok_score + spotify_score + cross_platform_bonus)
            plays = tiktok_posts if tiktok_posts > 0 else spotify_streams
            
        # EVERGREEN VIEW: Consistent daily streams
        else:  # view == "evergreen"
            # Need at least some historical data
            if len(all_metrics) < 2:
                continue
            
            # Calculate average daily streams
            total_streams = sum([m.spotify_streams or 0 for m in all_metrics])
            avg_daily_streams = total_streams / max(len(all_metrics), 1)
            
            # Evergreen criteria: consistent 10k+ daily streams
            if avg_daily_streams < 10000:
                continue
            
            # Calculate consistency (lower variance = higher score)
            streams_list = [m.spotify_streams or 0 for m in all_metrics if m.spotify_streams]
            if len(streams_list) < 2:
                continue
            
            mean_streams = sum(streams_list) / len(streams_list)
            variance = sum((x - mean_streams) ** 2 for x in streams_list) / len(streams_list)
            std_dev = variance ** 0.5
            coefficient_of_variation = (std_dev / mean_streams) if mean_streams > 0 else 1
            
            # Score based on average and consistency
            if avg_daily_streams >= 100000:
                trend_score = 95 - min(20, int(coefficient_of_variation * 100))
            elif avg_daily_streams >= 50000:
                trend_score = 85 - min(20, int(coefficient_of_variation * 100))
            elif avg_daily_streams >= 20000:
                trend_score = 75 - min(20, int(coefficient_of_variation * 100))
            else:
                trend_score = 65 - min(20, int(coefficient_of_variation * 100))
            
            plays = int(avg_daily_streams)
        
        # Determine platform label
        platform = "TikTok"
        if tiktok_posts > 0 and spotify_streams > 0:
            platform = "TikTok + Spotify"
        elif spotify_streams > 0:
            platform = "Spotify"
        
        songs.append({
            "id": track.id,
            "title": track.title,
            "artist": track.artist_name,
            "plays": plays,
            "trend_score": trend_score,
            "platform": platform,
            "has_label": False,
            "date_discovered": track.first_discovered.isoformat() if track.first_discovered else datetime.now().isoformat(),
            "tiktok_posts": tiktok_posts,
            "spotify_streams": spotify_streams,
            # Media & Links
            "image_url": track.image_url,
            "spotify_url": track.spotify_url,
            "tiktok_url": track.tiktok_url,
            "spotify_popularity": track.spotify_popularity
        })
    
    # Sort by trend score
    songs.sort(key=lambda x: x["trend_score"], reverse=True)
    
    # Apply pagination
    paginated_songs = songs[offset:offset+limit]
    
    return {
        "total": len(songs),
        "limit": limit,
        "offset": offset,
        "view": view,
        "songs": paginated_songs
    }


@router.get("/sounds")
async def get_trending_sounds(
    current_user: Dict = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get trending sounds/audio clips
    Requires authentication.
    """
    
    # TODO: Implement actual API logic
    mock_sounds = [
        {
            "id": f"sound_{i}",
            "name": f"Sound {i}",
            "usage_count": 500000 - (i * 5000),
            "trend_score": 90 - i,
            "platform": "TikTok",
            "date_discovered": datetime.now().isoformat()
        }
        for i in range(1, min(limit, 20) + 1)
    ]
    
    return {
        "total": len(mock_sounds),
        "limit": limit,
        "offset": offset,
        "sounds": mock_sounds
    }


@router.get("/filters")
async def get_available_filters():
    """
    Get available filter options for discover page
    """
    return {
        "types": ["viral", "rising", "new", "all"],
        "platforms": ["TikTok", "Instagram", "YouTube", "Spotify"],
        "genres": ["Pop", "Hip-Hop", "Electronic", "Rock", "R&B"],
        "time_ranges": ["24h", "7d", "30d", "all"]
    }


@router.get("/details/{item_id}")
async def get_item_details(
    item_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get detailed information about a specific song or sound
    Requires authentication.
    """
    
    # TODO: Implement actual lookup logic
    if not item_id:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Mock detailed data
    return {
        "id": item_id,
        "title": "Song/Sound Title",
        "artist": "Artist Name",
        "details": {
            "plays": 1500000,
            "likes": 250000,
            "shares": 50000,
            "comments": 12000,
            "trend_score": 92,
            "growth_rate": "+45%",
            "has_label": False,
            "contact_info": None,
            "platforms": ["TikTok", "Instagram"],
            "peak_date": datetime.now().isoformat()
        }
    }
