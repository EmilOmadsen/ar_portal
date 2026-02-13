"""
Song Analytics Endpoint
Detailed analytics for individual songs (TikTok or Spotify)
"""
from fastapi import APIRouter, Depends, Query, Response, Path
from typing import Dict, Optional
from app.core.security import get_current_user
from app.core.discovery.chartex_client import ChartexClient

router = APIRouter(
    prefix="/api/discovery/song-analytics",
    tags=["song-analytics"]
)


@router.get("/{platform}/{platform_id}/stats")
async def get_song_analytics(
    platform: str = Path(..., description="Platform: tiktok or spotify"),
    platform_id: str = Path(..., description="Platform-specific song/sound ID"),
    response: Response = None,
    current_user: Dict = Depends(get_current_user),
    history_days: int = Query(30, ge=7, le=90, description="Days of historical data")
):
    """
    Get comprehensive analytics for a song
    - TikTok: video counts, video views over time
    - Spotify: streaming stats over time
    - Cross-platform: linked TikTok sounds for Spotify tracks
    """
    # Add cache-control headers
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    chartex_client = ChartexClient()
    
    print(f"\n🎵 SONG ANALYTICS: {platform}/{platform_id} (history={history_days}d)")
    
    result = {
        "platform": platform,
        "platform_id": platform_id,
        "history_days": history_days
    }
    
    if platform == "spotify":
        # Fetch Spotify streaming stats
        spotify_stats = await chartex_client.get_song_stats(
            platform="spotify",
            platform_id=platform_id,
            metric="spotify-streams",
            limit_by_latest_days=history_days,
            mode="daily"
        )
        result["spotify_streams"] = spotify_stats
        
        # Fetch linked TikTok sounds
        linked_sounds = await chartex_client.get_linked_tiktok_sounds(
            spotify_id=platform_id,
            limit=10,
            sort_by="tiktok_total_video_count"
        )
        result["linked_tiktok_sounds"] = linked_sounds
        
    elif platform == "tiktok":
        # Fetch TikTok video counts over time
        video_counts = await chartex_client.get_tiktok_sound_stats(
            tiktok_sound_id=platform_id,
            metric="tiktok-video-counts",
            limit_by_latest_days=history_days,
            mode="daily"
        )
        result["video_counts"] = video_counts
        
        # Fetch TikTok video views over time (if available)
        video_views = await chartex_client.get_tiktok_sound_stats(
            tiktok_sound_id=platform_id,
            metric="tiktok-video-views",
            limit_by_latest_days=history_days,
            mode="daily"
        )
        result["video_views"] = video_views
    
    return result


@router.get("/{platform}/{platform_id}/videos")
async def get_song_videos(
    platform: str = Path(..., description="Platform: tiktok or spotify"),
    platform_id: str = Path(..., description="Platform-specific song/sound ID"),
    response: Response = None,
    current_user: Dict = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("tiktok_video_views", description="Sort: tiktok_video_views, tiktok_video_likes, etc."),
    country_code: Optional[str] = Query(None, description="Filter by creator country"),
    time_range: str = Query("all_time", description="Time range: all_time, 24hours, 7days"),
    min_views: Optional[int] = Query(None, description="Minimum video views")
):
    """
    Get top TikTok videos using this song/sound
    Works for both TikTok sounds and Spotify tracks
    """
    # Add cache-control headers
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    chartex_client = ChartexClient()
    
    page_number = (offset // limit) + 1
    fetch_limit = limit + 1
    
    print(f"\n🎬 SONG VIDEOS: {platform}/{platform_id} (sort={sort_by}, time_range={time_range})")
    
    videos = await chartex_client.get_song_videos(
        platform=platform,
        platform_id=platform_id,
        limit=fetch_limit,
        sort_by=sort_by,
        country_code=country_code,
        time_range=time_range,
        min_views=min_views,
        page=page_number
    )
    
    has_more = len(videos) > limit
    if has_more:
        videos = videos[:limit]
    
    return {
        "platform": platform,
        "platform_id": platform_id,
        "total": len(videos),
        "offset": offset,
        "limit": limit,
        "has_more": has_more,
        "videos": videos
    }


@router.get("/{platform}/{platform_id}/influencers")
async def get_song_influencers(
    platform: str = Path(..., description="Platform: tiktok or spotify"),
    platform_id: str = Path(..., description="Platform-specific song/sound ID"),
    response: Response = None,
    current_user: Dict = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("sum_tiktok_video_total_views_by_username"),
    country_code: Optional[str] = Query(None, description="Filter by influencer country")
):
    """
    Get top influencers who have used this song/sound
    Sorted by total views, number of videos, or follower count
    """
    # Add cache-control headers
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    chartex_client = ChartexClient()
    
    page_number = (offset // limit) + 1
    fetch_limit = limit + 1
    
    print(f"\n👥 SONG INFLUENCERS: {platform}/{platform_id} (sort={sort_by})")
    
    influencers = await chartex_client.get_song_influencers(
        platform=platform,
        platform_id=platform_id,
        limit=fetch_limit,
        sort_by=sort_by,
        country_code=country_code,
        page=page_number
    )
    
    has_more = len(influencers) > limit
    if has_more:
        influencers = influencers[:limit]
    
    return {
        "platform": platform,
        "platform_id": platform_id,
        "total": len(influencers),
        "offset": offset,
        "limit": limit,
        "has_more": has_more,
        "influencers": influencers
    }


@router.get("/{platform}/{platform_id}/countries")
async def get_song_countries(
    platform: str = Path(..., description="Platform: tiktok or spotify"),
    platform_id: str = Path(..., description="Platform-specific song/sound ID"),
    response: Response = None,
    current_user: Dict = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get country breakdown for this song
    Shows which countries have the most TikTok activity
    """
    # Add cache-control headers
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    chartex_client = ChartexClient()
    
    print(f"\n🌍 SONG COUNTRIES: {platform}/{platform_id}")
    
    countries = await chartex_client.get_song_countries(
        platform=platform,
        platform_id=platform_id,
        limit=limit
    )
    
    return {
        "platform": platform,
        "platform_id": platform_id,
        "total": len(countries),
        "countries": countries
    }
