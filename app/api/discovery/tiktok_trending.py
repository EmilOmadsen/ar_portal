"""
TikTok Trending Songs Discovery with Historical Time Series
Combines Chartex TikTok data with Spotify metrics and historical trends
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Response
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
from functools import lru_cache
import hashlib
import json
import logging
import sys

from app.db.session import SessionLocal
from app.core.security import get_current_user
from app.core.discovery.chartex_client import get_chartex_client
from app.core.discovery.spotify_client import SpotifyClient

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/discovery/tiktok-trending",
    tags=["discovery-tiktok"]
)

# Simple in-memory cache with configurable TTL
_response_cache = {}
_cache_ttl = 0  # DISABLED - No caching to force fresh API calls every time
_label_filter_cache_ttl = 0  # DISABLED - No caching for label queries either

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _matches_label_filter(label_text: str, label_type: str) -> bool:
    """Check if a label matches the given filter type"""
    label_text = label_text.lower()
    
    if label_type == "major":
        # Universal Music Group
        universal_labels = [
            "universal", "umg", "ume", "umc", "interscope", "capitol", 
            "republic", "def jam", "island", "motown", "geffen", "verve",
            "polydor", "emi", "virgin music", "ingrooves", "10k projects",
            "astralwerks", "darkroom", "quality control", "spinnin'",
            "blue note", "decca", "casablanca", "caroline",
            "aftermath", "222 records", "umg recordings",
            "distributed by virgin music"
        ]
        return any(term in label_text for term in universal_labels)
        
    elif label_type == "sony":
        # Sony Music Entertainment  
        sony_labels = [
            "sony", "columbia", "rca", "epic", "arista", "legacy",
            "the orchard", "awal", "alamo", "disruptor", "polo grounds",
            "relentless", "provident", "masterworks", "milan",
            "black butter", "insanity records", "dreamville",
            "ki/oon", "ki oon", "aniplex"
        ]
        return any(term in label_text for term in sony_labels)
        
    elif label_type == "warner":
        # Warner Music Group
        warner_labels = [
            "warner", "wmg", "wea", "atlantic", "elektra", "parlophone",
            "300 entertainment", "asylum", "big beat", "lava",
            "fueled by ramen", "roadrunner", "reprise", "sire",
            "east west", "nonesuch", "ada"
        ]
        return any(term in label_text for term in warner_labels)
        
    elif label_type == "bmg":
        # BMG Rights Management
        bmg_labels = [
            "bmg", "rise records", "vagrant", "s-curve", "infectious",
            "bbr music", "broken bow", "stoney creek", "wheelhouse"
        ]
        return any(term in label_text for term in bmg_labels)
        
    elif label_type == "indie":
        # Major Indie Labels
        indie_labels = [
            "xl recordings", "4ad", "matador", "rough trade", "beggars",
            "secretly canadian", "jagjaguwar", "dead oceans",
            "domino recording", "pias", "mute records", "empire",
            "monstercat", "ultra music", "mad decent", "stones throw",
            "brainfeeder", "ninja tune", "warp", "epitaph", "anti-",
            "sub pop", "believe", "kobalt", "merlin", "onerpm",
            "distrokid", "tunecore", "cd baby", "ditto"
        ]
        return any(term in label_text for term in indie_labels)
        
    elif label_type == "unsigned":
        # Exclude ALL known labels
        all_known_labels = [
            "universal", "umg", "interscope", "capitol", "republic", "def jam",
            "sony", "columbia", "rca", "epic", "arista",
            "warner", "atlantic", "elektra", "parlophone",
            "bmg", "empire", "believe", "kobalt", "distrokid"
        ]
        # Include if label is empty or doesn't match any known label
        if not label_text or label_text in ["none", "unknown"]:
            return True
        return not any(known in label_text for known in all_known_labels)
    
    return False


@router.get("/songs")
async def get_trending_songs_with_history(
    response: Response,
    current_user: Dict = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100, description="Number of songs to return (default 10 for faster loading)"),
    offset: int = Query(0, ge=0, description="Number of songs to skip (for pagination)"),
    sort_by: str = Query(
        "tiktok_last_24_hours_video_count",
        description="Sort field: tiktok_total_video_count, tiktok_last_7_days_video_count, tiktok_last_24_hours_video_count, spotify_streams"
    ),
    tiktok_metric: Optional[str] = Query(None, description="TikTok time period for Chartex fetch: tiktok_last_24_hours_video_count, tiktok_last_7_days_video_count, tiktok_total_video_count"),
    spotify_sort_metric: Optional[str] = Query(None, description="Spotify sorting: daily_streams, weekly_streams, total_streams"),
    min_video_count: Optional[int] = Query(None, description="Minimum TikTok video count"),
    country_code: Optional[str] = Query(None, description="Country code (e.g., US, GB, DE or empty for worldwide)"),
    country_codes: Optional[str] = Query(None, description="Legacy param - use country_code instead"),
    label_type: Optional[str] = Query(None, description="Label type filter: major, sony, warner, bmg, indie, unsigned"),
    search: Optional[str] = Query(None, description="Search term"),
    include_history: bool = Query(True, description="Include historical TikTok time series data"),
    history_days: int = Query(3, ge=1, le=90, description="Days of historical data to fetch (default 3 for faster loading)"),
    include_spotify_metadata: bool = Query(False, description="Include Spotify metadata (slower but more details)")
):
    """
    Get trending songs from TikTok with:
    - Current TikTok metrics (videos, sounds, growth)
    - Spotify data (popularity, images, streams if available)
    - Historical time series for TikTok and Spotify metrics (7 days by default)
    
    Perfect for discovering viral tracks and analyzing their growth trajectory.
    """
    logger.info(f"\n🔍 API CALLED with sort_by={sort_by}, tiktok_metric={tiktok_metric}, country_code={country_code}")
    logger.info(f"🔍 Current time: {datetime.now()}")
    logger.info(f"🔍 Cache size: {len(_response_cache)} items")
    try:
        # FORCE FRESH DATA - Skip cache entirely
        # Clear the entire cache on every request to guarantee fresh data
        _response_cache.clear()
        logger.info(f"🧹 Cache cleared - will fetch fresh data from Chartex")
        
        chartex_client = get_chartex_client()
        spotify_client = None
        
        # Always initialize Spotify client if we're sorting by Spotify OR if metadata is requested
        from app.core.config import settings
        if (sort_by == "spotify_streams" or include_spotify_metadata) and settings.SPOTIFY_CLIENT_ID and settings.SPOTIFY_CLIENT_SECRET:
            spotify_client = SpotifyClient()
        
        # Use country_code if provided, fallback to country_codes for backwards compatibility
        country_param = country_code or country_codes
        
        # Fetch songs from Chartex based on sorting strategy
        # Priority: Spotify sorting > Label filtering > Normal pagination
        
        if sort_by == "spotify_streams":
            # For Spotify sorting, ALWAYS fetch a large batch upfront (regardless of label filter)
            # because we need to enrich with Spotify data, then filter/sort locally
            fetch_limit = 200  # Large batch to ensure enough songs after filtering
            page_number = 1
            has_more_available = False
            # Use tiktok_metric parameter for Chartex fetch (respects time period filter)
            chartex_sort_by = tiktok_metric if tiktok_metric else "tiktok_last_7_days_video_count"
            logger.info(f"📥 Fetching {fetch_limit} songs for Spotify sorting (TikTok metric: {chartex_sort_by})")
            logger.info(f"   Label filter '{label_type}' will be applied after enrichment" if label_type else "   No label filter")
            
            songs = await chartex_client.get_songs(
                limit=fetch_limit,
                sort_by=chartex_sort_by,
                min_video_count=min_video_count,
                search=search,
                country_codes=country_param,
                page=page_number,
                force_refresh=True
            )
            
        elif label_type:
            # If label filter is applied (and NOT Spotify sorting), paginate through Chartex for matches
            logger.info(f"🏷️  Label filter active: {label_type}")
            logger.info(f"   Will fetch songs until we have {limit + offset} matches")
            
            all_songs = []
            page_num = 1
            batch_size = 50  # Fetch 50 at a time
            max_pages = 20  # Safety limit - stop after 1000 songs (20 * 50)
            has_more_available = False
            
            # Keep fetching until we have enough songs (limit + offset + 1 to check if more exist)
            target_count = limit + offset + 1  # Fetch one extra to check if more exist
            
            while len(all_songs) < target_count and page_num <= max_pages:
                logger.info(f"   Fetching page {page_num} (batch of {batch_size})...")
                batch_songs = await chartex_client.get_songs(
                    limit=batch_size,
                    sort_by=sort_by,
                    min_video_count=min_video_count,
                    search=search,
                    country_codes=country_param,
                    page=page_num
                )
                
                if not batch_songs:
                    logger.info(f"   No more songs available from Chartex")
                    break
                
                # Log first song's label fields on first batch for debugging
                if page_num == 1 and batch_songs:
                    s = batch_songs[0]
                    logger.info(f"   🏷️ First song label fields: label_name={s.get('label_name')}, label={s.get('label')}, distributor={s.get('distributor')}")
                
                # Filter this batch by label
                for song in batch_songs:
                    label = str(song.get("label_name") or song.get("label") or song.get("distributor") or "").lower()
                    
                    # Check if this song matches the label filter
                    if _matches_label_filter(label, label_type):
                        all_songs.append(song)
                        
                        # Stop early if we have enough (including the extra one)
                        if len(all_songs) >= target_count:
                            has_more_available = True
                            break
                
                logger.info(f"   Found {len(all_songs)} matching songs so far")
                page_num += 1
            
            # If we fetched more than needed, there are definitely more available
            if len(all_songs) > (limit + offset):
                has_more_available = True
            
            songs = all_songs
            logger.info(f"   ✅ Total filtered songs: {len(songs)}, has_more: {has_more_available}")
        else:
            # No label filter and no Spotify sorting - normal pagination
            has_more_available = False
            fetch_limit = limit  # Use exact limit to avoid pagination gaps
            # Calculate which page to fetch from Chartex (1-based)
            page_number = (offset // limit) + 1
            chartex_sort_by = sort_by
            logger.info(f"📥 Fetching {fetch_limit} songs from Chartex page {page_number} (sort_by={chartex_sort_by})")
            
            songs = await chartex_client.get_songs(
                limit=fetch_limit,
                sort_by=chartex_sort_by,
                min_video_count=min_video_count,
                search=search,
                country_codes=country_param,
                page=page_number,
                force_refresh=True  # Always force fresh data from Chartex
            )

            
            # If we got a full page, there are likely more available
            has_more_available = len(songs) >= limit
            
            logger.info(f"   ✅ Fetched {len(songs)} songs (page {page_number}, offset {offset}), has_more: {has_more_available}")
        
        # Fetch history based on sorting mode:
        # - For Spotify sorting: always fetch (we need it for sorting even with label filter)
        # - Always fetch if include_history is true so Spotify streams show in the table
        fetch_history = include_history
        
        if not songs:
            return {
                "total": 0,
                "songs": [],
                "filters": {
                    "sort_by": sort_by,
                    "country_codes": country_codes,
                    "min_video_count": min_video_count
                }
            }
        
        # Enrich each song with Spotify and historical data (in parallel for better performance)
        enriched_songs = []
        
        # Process all songs in parallel
        enrichment_tasks = []
        for song in songs:
            # Debug: Log first song structure to see available fields
            if len(enrichment_tasks) == 0:
                logger.info(f"🔍 First song raw data from Chartex:")
                logger.info(f"   Available keys: {list(song.keys())}")
                logger.info(f"   tiktok_sound_id: {song.get('tiktok_sound_id')}")
                logger.info(f"   id: {song.get('id')}")
                logger.info(f"   spotify_id: {song.get('spotify_id')}")
                logger.info(f"   label_name: {song.get('label_name')}")
                logger.info(f"   label: {song.get('label')}")
                logger.info(f"   distributor: {song.get('distributor')}")
            
            # Use fetch_history variable to control whether to fetch historical data
            enrichment_tasks.append(_enrich_song(song, spotify_client, chartex_client, fetch_history, history_days))
        
        enriched_songs = await asyncio.gather(*enrichment_tasks)
        
        # Apply label filter on enriched songs only for spotify_streams path
        # (the label_type path already pre-filtered before enrichment)
        if label_type and sort_by == "spotify_streams":
            logger.info(f"🏷️  Applying label filter: {label_type} (post-enrichment for Spotify sorting)")
            original_count = len(enriched_songs)
            enriched_songs = [
                song for song in enriched_songs
                if _matches_label_filter(str(song.get("record_label") or song.get("label") or "").lower(), label_type)
            ]
            logger.info(f"   ✅ Filtered from {original_count} to {len(enriched_songs)} songs matching '{label_type}' label")
        
        # Sort by Spotify streams if requested
        if sort_by == "spotify_streams" and spotify_sort_metric:
            logger.info(f"🎵 Sorting by Spotify metric: {spotify_sort_metric}")
            
            # Filter out songs without Spotify data
            songs_with_spotify = [
                song for song in enriched_songs 
                if song.get('history') and song['history'].get('spotify') and 
                (song['history']['spotify'].get('streams') or song['history']['spotify'].get('total_streams', 0) > 0)
            ]
            
            logger.info(f"📊 Filtered to {len(songs_with_spotify)} songs with Spotify data (from {len(enriched_songs)} total)")
            
            def get_spotify_sort_value(song):
                if not song.get('history') or not song['history'].get('spotify'):
                    return 0
                streams = song['history']['spotify'].get('streams', [])
                total_streams = song['history']['spotify'].get('total_streams', 0)
                
                if spotify_sort_metric == 'daily_streams':
                    # Most recent day's streams
                    return streams[-1].get('value', 0) if streams else 0
                elif spotify_sort_metric == 'weekly_streams':
                    # Last 7 days total
                    last_7 = streams[-7:] if len(streams) >= 7 else streams
                    return sum(day.get('value', 0) for day in last_7)
                elif spotify_sort_metric == 'total_streams':
                    # All-time total
                    return total_streams
                return 0
            
            songs_with_spotify.sort(key=get_spotify_sort_value, reverse=True)
            enriched_songs = songs_with_spotify  # Replace with filtered & sorted list
            logger.info(f"✅ Sorted {len(enriched_songs)} songs by {spotify_sort_metric}")
        
        # For label-filtered queries OR Spotify-sorted queries, apply offset and limit locally
        # For non-filtered queries, we already fetched the right page from Chartex
        if label_type or sort_by == "spotify_streams":
            # Apply offset and limit to support pagination
            final_songs = enriched_songs[offset:offset + limit]
            total_available = len(enriched_songs)
            # Check if there are more songs beyond what we're showing
            has_more = (offset + limit) < len(enriched_songs)
        else:
            # Already fetched the correct page from Chartex, no need to slice
            has_more = has_more_available
            final_songs = enriched_songs
            total_available = len(enriched_songs)  # This is approximate for non-filtered
        
        # Note: has_more is already computed above based on the filtering logic
        
        logger.info(f"🔍 Final pagination state: has_more={has_more}")
        logger.info(f"   - filtered/sorted locally: {label_type or sort_by == 'spotify_streams'}")
        logger.info(f"   - offset: {offset}, limit: {limit}, total_available: {total_available}")
        logger.info(f"   - returning {len(final_songs)} songs")

        
        response_data = {
            "total": len(final_songs),
            "total_available": total_available,
            "offset": offset,
            "limit": limit,
            "has_more": has_more,
            "filters": {
                "sort_by": sort_by,
                "country_codes": country_codes,
                "min_video_count": min_video_count,
                "label_type": label_type,
                "history_days": history_days if include_history else None
            },
            "songs": final_songs
        }
        
        # Don't cache - always fetch fresh
        # _response_cache[cache_key] = (response_data, datetime.now().timestamp())
        
        # Set cache control headers to prevent browser caching
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        
        return response_data
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching trending songs: {str(e)}"
        )


@router.get("/songs/{song_id}/history")
async def get_song_history(
    song_id: str,
    current_user: Dict = Depends(get_current_user),
    days: int = Query(30, ge=7, le=90, description="Days of historical data"),
    metrics: str = Query(
        "all",
        description="Metrics to fetch: all, tiktok, spotify (Spotify data available via Chartex!)"
    )
):
    """
    Get detailed historical time series for a specific song
    
    Returns daily data points for:
    - TikTok video counts (daily new videos using this sound)
    - TikTok video views (cumulative views)
    - Spotify streams (daily streams via Chartex)
    """
    try:
        chartex_client = get_chartex_client()
        
        # Get song details first
        song = await chartex_client.get_song_detail(song_id)
        if not song:
            raise HTTPException(status_code=404, detail="Song not found")
        
        tiktok_sound_id = song.get("tiktok_sound_id")
        spotify_id = song.get("spotify_id")
        
        history = await _fetch_historical_data(
            chartex_client=chartex_client,
            tiktok_sound_id=tiktok_sound_id,
            spotify_id=spotify_id if metrics in ["all", "spotify"] else None,
            days=days,
            fetch_tiktok=metrics in ["all", "tiktok"]
        )
        
        return {
            "song": {
                "id": song_id,
                "title": song.get("title"),
                "artist": song.get("artist"),
                "tiktok_sound_id": tiktok_sound_id,
                "spotify_id": spotify_id
            },
            "history": history,
            "period": {
                "days": days,
                "metrics": metrics
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching song history: {str(e)}"
        )


async def _enrich_song(song: Dict, spotify_client, chartex_client, include_history: bool, history_days: int) -> Dict:
    """Helper function to enrich a single song with Spotify and historical data"""
    # Extract song ID - try multiple possible fields from Chartex API
    song_id = (
        song.get("id") or 
        song.get("song_id") or 
        song.get("chartex_id") or 
        song.get("spotify_id") or
        str(song.get("tiktok_sound_id", ""))
    )
    
    # Get TikTok sound ID - either from song data or fetch via Spotify ID
    tiktok_sound_id = song.get("tiktok_sound_id")
    spotify_id = song.get("spotify_id")
    
    # If we have Spotify ID but no TikTok sound ID, fetch it
    if spotify_id and not tiktok_sound_id and chartex_client:
        try:
            logger.info(f"🔍 Fetching TikTok sound ID for Spotify track: {spotify_id}")
            tiktok_sounds = await chartex_client.get_tiktok_sounds_for_song(spotify_id, limit=1)
            if tiktok_sounds and "data" in tiktok_sounds:
                items = tiktok_sounds["data"].get("items", [])
                if items and len(items) > 0:
                    tiktok_sound_id = items[0].get("tiktok_sound_id")
                    logger.info(f"✅ Found TikTok sound ID: {tiktok_sound_id}")
                    # Also update the song metrics with fresh data
                    song["tiktok_sound_id"] = tiktok_sound_id
                    song["tiktok_total_video_count"] = items[0].get("tiktok_total_video_count")
                    song["tiktok_last_7_days_video_count"] = items[0].get("tiktok_last_7_days_video_count")
                    song["tiktok_last_24_hours_video_count"] = items[0].get("tiktok_last_24_hours_video_count")
        except Exception as e:
            logger.info(f"⚠️  Error fetching TikTok sound ID: {e}")
    
    enriched_song = {
        "id": song_id,
        "title": song.get("title", song.get("song_name")),
        "artist": song.get("artist", song.get("artists")),
        "album_image": song.get("song_image_url"),
        "spotify_id": spotify_id,  # Store at top level for easy access
        "tiktok_sound_id": tiktok_sound_id,  # Store at top level for easy access
        "label": song.get("label_name") or song.get("label"),  # Record label from Chartex
        "distributor": song.get("distributor"),  # Distributor information
        "record_label": song.get("label_name") or song.get("label") or song.get("distributor") or None,  # Combined label field
        "tiktok_metrics": {
            "total_videos": song.get("tiktok_total_video_count"),
            "last_7_days_videos": song.get("tiktok_last_7_days_video_count"),
            "last_24h_videos": song.get("tiktok_last_24_hours_video_count"),
            "last_24h_percentage": song.get("tiktok_last_24_hours_video_percentage"),
            "total_sounds": song.get("tiktok_total_sound_count"),
            "sound_id": tiktok_sound_id
        },
        "spotify": None,
        "history": None
    }
    
    # Get Spotify data if available
    spotify_id = song.get("spotify_id")
    if spotify_id and spotify_client:
        try:
            spotify_data = await spotify_client.get_track(spotify_id)
            if spotify_data:
                enriched_song["spotify"] = {
                    "id": spotify_id,
                    "url": spotify_data.get("external_urls", {}).get("spotify"),
                    "popularity": spotify_data.get("popularity"),
                    "album_image": spotify_data.get("album", {}).get("images", [{}])[0].get("url") if spotify_data.get("album", {}).get("images") else None,
                    "release_date": spotify_data.get("album", {}).get("release_date"),
                    "duration_ms": spotify_data.get("duration_ms"),
                    "preview_url": spotify_data.get("preview_url")
                }
        except Exception as e:
            logger.info(f"⚠️ Error fetching Spotify data for {spotify_id}: {e}")
    
    # Get historical data if requested
    if include_history:
        history = await _fetch_historical_data(
            chartex_client=chartex_client,
            tiktok_sound_id=song.get("tiktok_sound_id"),
            spotify_id=spotify_id,
            days=history_days
        )
        enriched_song["history"] = history
    
    return enriched_song


async def _fetch_historical_data(
    chartex_client,
    tiktok_sound_id: Optional[str],
    spotify_id: Optional[str],
    days: int = 30,
    fetch_tiktok: bool = True
) -> Dict[str, Any]:
    """
    Fetch historical time series data for TikTok and Spotify metrics via Chartex
    
    Returns structured data with daily data points for visualization.
    Note: Spotify streaming data IS available through Chartex API!
    """
    history = {
        "tiktok": {
            "video_counts": None,
            "video_views": None
        },
        "spotify": {
            "streams": None,
            "total_streams": 0
        }
    }
    
    # Fetch TikTok historical data
    if fetch_tiktok and tiktok_sound_id:
        try:
            # TikTok Video Counts (daily new videos using this sound)
            video_counts = await chartex_client.get_song_stats(
                platform_id=tiktok_sound_id,
                platform="tiktok",
                metric="tiktok-video-counts",
                mode="daily",
                limit_by_latest_days=days
            )
            
            if video_counts and "results" in video_counts:
                history["tiktok"]["video_counts"] = _format_time_series(
                    video_counts["results"],
                    value_key="value"
                )
            
            # TikTok Video Views (cumulative views)
            video_views = await chartex_client.get_song_stats(
                platform_id=tiktok_sound_id,
                platform="tiktok",
                metric="tiktok-video-views",
                mode="total",
                limit_by_latest_days=days
            )
            
            if video_views and "results" in video_views:
                history["tiktok"]["video_views"] = _format_time_series(
                    video_views["results"],
                    value_key="value"
                )
        
        except Exception as e:
            logger.info(f"⚠️ Error fetching TikTok history for {tiktok_sound_id}: {e}")
    
    # Fetch Spotify historical streaming data via Chartex
    if spotify_id:
        try:
            logger.info(f"🎵 Fetching Spotify streaming data for {spotify_id}")
            spotify_streams = await chartex_client.get_song_stats(
                platform_id=spotify_id,
                platform="spotify",
                metric="spotify-streams",
                mode="daily",
                limit_by_latest_days=days
            )
            
            logger.info(f"📊 Spotify streams response: {spotify_streams}")
            
            if spotify_streams and "data" in spotify_streams:
                data_obj = spotify_streams["data"]
                
                # Capture total all-time streams
                total_streams = data_obj.get("spotify_total_streams", 0)
                
                # The Chartex API returns: {"data": {"stream_counts": [...], "spotify_total_streams": X}}
                if "stream_counts" in data_obj and data_obj["stream_counts"]:
                    logger.info(f"✅ Found {len(data_obj['stream_counts'])} Spotify stream data points")
                    logger.info(f"✅ Total all-time streams: {total_streams}")
                    
                    # Convert stream_counts to our format
                    formatted_streams = []
                    for item in data_obj["stream_counts"]:
                        formatted_streams.append({
                            "date": item.get("date"),
                            "value": item.get("spotify_stream_count", 0)
                        })
                    
                    history["spotify"]["streams"] = formatted_streams
                    history["spotify"]["total_streams"] = total_streams  # Add total all-time streams
                    logger.info(f"✅ Formatted {len(formatted_streams)} Spotify streams with total: {total_streams}")
                else:
                    logger.info(f"⚠️ No stream_counts in Spotify response")
                    # Even if no daily data, capture total if available
                    if total_streams > 0:
                        history["spotify"]["total_streams"] = total_streams

            else:
                logger.info(f"❌ No data in Spotify response")
        
        except Exception as e:
            logger.info(f"⚠️ Error fetching Spotify history for {spotify_id}: {e}")
    
    return history


def _format_time_series(data: List[Dict], value_key: str = "value") -> List[Dict]:
    """
    Format time series data for frontend consumption
    
    Input format from Chartex:
    [{"date": "2026-01-15", "value": 1234}, ...]
    
    Output format:
    [{"date": "2026-01-15", "value": 1234}, ...]
    """
    if not data:
        return []
    
    formatted = []
    for point in data:
        formatted.append({
            "date": point.get("date"),
            "value": point.get(value_key, 0)
        })
    
    # Sort by date ascending (oldest first)
    formatted.sort(key=lambda x: x["date"])
    
    return formatted


def _format_time_series_flexible(data: List[Dict]) -> List[Dict]:
    """
    Flexible formatter that tries multiple possible field names
    """
    if not data:
        return []
    
    formatted = []
    for point in data:
        # Try different date field names
        date = point.get("date") or point.get("timestamp") or point.get("day")
        
        # Try different value field names
        value = (
            point.get("value") or 
            point.get("count") or 
            point.get("video_count") or
            point.get("tiktok_video_count") or  # Chartex uses this field name
            point.get("spotify_stream_count") or
            point.get("streams") or
            0
        )
        
        if date:
            formatted.append({
                "date": date,
                "value": value
            })
    
    # Sort by date ascending (oldest first)
    formatted.sort(key=lambda x: x["date"])
    
    return formatted


@router.get("/{song_id}/analytics")
async def get_song_analytics(
    song_id: str,
    current_user: Dict = Depends(get_current_user),
    days: int = Query(30, ge=7, le=90, description="Days of historical data"),
    tiktok_sound_id: Optional[str] = Query(None, description="TikTok sound ID"),
    spotify_id: Optional[str] = Query(None, description="Spotify track ID"),
    title: Optional[str] = Query(None, description="Song title"),
    artist: Optional[str] = Query(None, description="Artist name")
):
    """
    Get comprehensive analytics for a specific song including:
    - TikTok creates timeline (daily video counts)
    - Top markets by TikTok creates (country breakdown)
    - Top markets by Spotify streams (country breakdown)
    - Combined market view showing both metrics
    
    Note: Since Chartex song detail endpoint may not work with all IDs,
    we accept tiktok_sound_id and spotify_id as query parameters
    """
    try:
        chartex_client = get_chartex_client()
        
        # Try to get song metadata from Chartex for totals
        song_metadata = None
        if not tiktok_sound_id and not spotify_id:
            song_detail = await chartex_client.get_song_detail(song_id)
            if song_detail:
                song_data = song_detail.get("data", {})
                song_metadata = song_data
                tiktok_sound_id = song_data.get("tiktok_sound_id")
                spotify_id = song_data.get("spotify_id")
                if not title:
                    title = song_data.get("title", "Unknown")
                if not artist:
                    artist = song_data.get("artist_name", "Unknown Artist")
        
        # If we have a TikTok sound ID, fetch its metadata for totals
        if tiktok_sound_id and not song_metadata:
            tiktok_sounds = await chartex_client.get_tiktok_sounds_for_song(spotify_id, limit=1) if spotify_id else None
            if tiktok_sounds and "data" in tiktok_sounds:
                items = tiktok_sounds["data"].get("items", [])
                if items and len(items) > 0:
                    song_metadata = items[0]
        
        # If still no IDs, return error
        if not tiktok_sound_id and not spotify_id:
            raise HTTPException(
                status_code=404, 
                detail="Song not found. Please provide tiktok_sound_id or spotify_id."
            )
        
        # Use provided title/artist or defaults
        title = title or "Unknown"
        artist = artist or "Unknown Artist"
        
        # Fetch TikTok creates timeline
        tiktok_timeline = []
        if tiktok_sound_id:
            logger.info(f"📊 Fetching TikTok video counts for TikTok sound ID: {tiktok_sound_id}")
            tiktok_stats = await chartex_client.get_song_stats(
                platform_id=str(tiktok_sound_id),
                platform="tiktok",
                metric="tiktok-video-counts",
                mode="daily",
                limit_by_latest_days=days
            )
            logger.info(f"📊 TikTok stats raw response: {tiktok_stats}")
            
            if tiktok_stats:
                # Try different possible response structures
                data_obj = tiktok_stats.get("data", tiktok_stats)
                
                # Look for video_counts, stream_counts, results, or items
                counts = (
                    data_obj.get("video_counts") or 
                    data_obj.get("stream_counts") or 
                    data_obj.get("results") or
                    data_obj.get("items") or
                    []
                )
                
                logger.info(f"📊 TikTok counts extracted: {len(counts)} items")
                if counts and len(counts) > 0:
                    logger.info(f"📊 First TikTok data point: {counts[0]}")
                    # Try different value keys
                    tiktok_timeline = _format_time_series_flexible(counts)
                    logger.info(f"📊 Formatted TikTok timeline: {len(tiktok_timeline)} points")
            else:
                logger.info(f"⚠️ No TikTok stats data returned")
        
        # Fetch Spotify streams timeline
        spotify_timeline = []
        if spotify_id:
            logger.info(f"🎵 Fetching Spotify stats for track_id: {spotify_id}")
            spotify_stats = await chartex_client.get_song_stats(
                platform_id=spotify_id,
                platform="spotify",
                metric="spotify-streams",
                mode="daily",
                limit_by_latest_days=days
            )
            logger.info(f"🎵 Spotify stats raw response: {spotify_stats}")
            
            if spotify_stats:
                data_obj = spotify_stats.get("data", spotify_stats)
                
                # Look for stream_counts, results, or items
                counts = (
                    data_obj.get("stream_counts") or 
                    data_obj.get("results") or
                    data_obj.get("items") or
                    []
                )
                
                logger.info(f"🎵 Spotify counts extracted: {len(counts)} items")
                if counts and len(counts) > 0:
                    logger.info(f"🎵 First Spotify data point: {counts[0]}")
                    spotify_timeline = _format_time_series_flexible(counts)
                    logger.info(f"🎵 Formatted Spotify timeline: {len(spotify_timeline)} points")
                    if spotify_timeline and len(spotify_timeline) > 0:
                        logger.info(f"🎵 First formatted point: {spotify_timeline[0]}")
            else:
                logger.info(f"⚠️ No Spotify stats data returned")
        
        # Get market breakdowns (if available from song data)
        # Note: Market breakdowns might not be available for all songs
        tiktok_markets = {}
        spotify_markets = {}
        
        # Format market data for charts (top 10 countries)
        top_tiktok_markets = []
        top_spotify_markets = []
        
        # Combine markets for comparison view
        top_combined_markets = []
        
        # Calculate totals - use metadata if available, otherwise calculate from timeline
        if song_metadata:
            tiktok_total = song_metadata.get("tiktok_total_video_count", 0)
            tiktok_last_7d = song_metadata.get("tiktok_last_7_days_video_count", 0)
            tiktok_last_24h = song_metadata.get("tiktok_last_24_hours_video_count", 0)
        else:
            tiktok_total = sum(point["value"] for point in tiktok_timeline) if tiktok_timeline else 0
            tiktok_last_7d = sum(point["value"] for point in tiktok_timeline[-7:]) if len(tiktok_timeline) >= 7 else tiktok_total
            tiktok_last_24h = tiktok_timeline[-1]["value"] if tiktok_timeline else 0
        
        return {
            "song": {
                "id": song_id,
                "title": title,
                "artist": artist,
                "spotify_id": spotify_id,
                "tiktok_sound_id": tiktok_sound_id
            },
            "timelines": {
                "tiktok_creates": tiktok_timeline,
                "spotify_streams": spotify_timeline
            },
            "markets": {
                "top_tiktok": top_tiktok_markets,
                "top_spotify": top_spotify_markets,
                "combined": top_combined_markets
            },
            "totals": {
                "tiktok_total_videos": tiktok_total,
                "tiktok_last_7d": tiktok_last_7d,
                "tiktok_last_24h": tiktok_last_24h
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching song analytics: {str(e)}"
        )


@router.post("/refresh-cache")
async def manual_refresh_cache(user: dict = Depends(get_current_user)):
    """
    Manually refresh the TikTok trending data cache.
    Clears cached data to force fresh fetch from Chartex on next request.
    """
    try:
        global _response_cache
        _response_cache.clear()
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🔄 Manual cache refresh triggered at {datetime.now()}")
        
        return {
            "success": True,
            "message": "Cache cleared successfully. Fresh data will be fetched on next request.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")


@router.get("/force-refresh-chartex")
async def force_refresh_chartex_data():
    """
    Force a complete refresh of Chartex data.
    This clears ALL caches and forces fresh API calls to Chartex.
    No authentication required - useful for testing/debugging.
    """
    try:
        logger.info("🚀🚀🚀 FORCE REFRESH TRIGGERED 🚀🚀🚀")
        _response_cache.clear()
        logger.info("✅ All caches cleared successfully")
        logger.info("✅ Next request will fetch completely fresh data from Chartex API")
        
        return {
            "success": True,
            "message": "All caches cleared. Next API call will fetch completely fresh data from Chartex.",
            "timestamp": datetime.now().isoformat(),
            "next_step": "Call /api/discovery/tiktok-trending/songs to fetch fresh data"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error forcing refresh: {str(e)}")
