"""
TikTok Creators/Influencers Discovery Endpoints
Fetch trending creators and their analytics
"""
from fastapi import APIRouter, Depends, Query, Response
from typing import Dict, Optional
from app.core.security import get_current_user
from app.core.discovery.chartex_client import ChartexClient

router = APIRouter(
    prefix="/api/discovery/creators",
    tags=["creators"]
)


@router.get("/list")
async def get_trending_creators(
    response: Response,
    current_user: Dict = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100, description="Number of creators to return"),
    offset: int = Query(0, ge=0, description="Number of creators to skip"),
    sort_by: str = Query("total_followers", description="Sort field: total_followers, last_7_days_followers_count"),
    country_code: Optional[str] = Query(None, description="Country code filter (e.g., US, GB, DK)"),
    search: Optional[str] = Query(None, description="Search term for creator name/username")
):
    """
    Get trending TikTok creators/influencers
    Sorted by follower count or recent growth
    """
    # Add cache-control headers
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    chartex_client = ChartexClient()
    
    # Calculate Chartex pagination
    page_number = (offset // limit) + 1
    fetch_limit = limit + 1  # Fetch one extra to check if more exist
    
    print(f"\n🎭 CREATORS API: Fetching creators (sort_by={sort_by}, country={country_code})")
    
    # Fetch creators from Chartex
    creators = await chartex_client.get_creators(
        limit=fetch_limit,
        sort_by=sort_by,
        country_code=country_code,
        search=search,
        page=page_number,
        force_refresh=True
    )
    
    # Check if more results exist
    has_more = len(creators) > limit
    if has_more:
        creators = creators[:limit]
    
    return {
        "total": len(creators),
        "offset": offset,
        "limit": limit,
        "has_more": has_more,
        "sort_by": sort_by,
        "creators": creators
    }


@router.get("/{username}/stats")
async def get_creator_stats(
    username: str,
    response: Response,
    current_user: Dict = Depends(get_current_user),
    history_days: int = Query(30, ge=7, le=90, description="Days of historical data")
):
    """
    Get detailed stats for a specific TikTok creator
    - Follower growth over time
    - Account metadata
    """
    # Add cache-control headers
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    chartex_client = ChartexClient()
    
    print(f"\n📊 CREATOR STATS: Fetching data for @{username}")
    
    # Fetch creator metadata and follower stats in parallel
    metadata = await chartex_client.get_creator_metadata(username)
    follower_stats = await chartex_client.get_creator_follower_stats(
        username=username,
        limit_by_latest_days=history_days,
        mode="daily"
    )
    
    return {
        "username": username,
        "metadata": metadata,
        "follower_history": follower_stats,
        "history_days": history_days
    }


@router.get("/{username}/videos")
async def get_creator_videos(
    username: str,
    response: Response,
    current_user: Dict = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("tiktok_video_views", description="Sort: tiktok_video_views, tiktok_video_likes, etc."),
    min_views: Optional[int] = Query(None, description="Minimum video views")
):
    """
    Get top videos from a creator
    Sorted by views, likes, or engagement
    """
    # Add cache-control headers
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    chartex_client = ChartexClient()
    
    page_number = (offset // limit) + 1
    fetch_limit = limit + 1
    
    print(f"\n🎬 CREATOR VIDEOS: Fetching for @{username} (sort={sort_by})")
    
    videos = await chartex_client.get_creator_videos(
        username=username,
        limit=fetch_limit,
        sort_by=sort_by,
        min_views=min_views,
        page=page_number
    )
    
    has_more = len(videos) > limit
    if has_more:
        videos = videos[:limit]
    
    return {
        "username": username,
        "total": len(videos),
        "offset": offset,
        "limit": limit,
        "has_more": has_more,
        "videos": videos
    }
