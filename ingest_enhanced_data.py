"""
Enhanced Data Ingestion - Fetches both TikTok AND Spotify streaming data
Plus historical metrics for evergreen detection
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.discovery import Track, TrackMetric, DiscoveryRun
from app.core.discovery.chartmetric import get_chartmetric_client
from app.core.discovery.label_detection import LabelDetector
import httpx


async def fetch_tiktok_charts(client, token: str, date: str = None) -> list:
    """Fetch TikTok trending tracks"""
    if not date:
        date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = await client.get(
            f"https://api.chartmetric.com/api/charts/tiktok/tracks?date={date}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            tracks = data.get("obj", [])
            return tracks if isinstance(tracks, list) else []
        else:
            print(f"   ⚠️  TikTok charts returned {response.status_code}")
            return []
    except Exception as e:
        print(f"   ❌ Error fetching TikTok charts: {e}")
        return []


async def fetch_spotify_track_stats(client, token: str, track_id: str, days: int = 30) -> dict:
    """
    Fetch Spotify streaming statistics for a track
    Returns recent streaming data to detect trends and calculate averages
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Try track stats endpoint
    try:
        # Get recent stats (last 30 days)
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        response = await client.get(
            f"https://api.chartmetric.com/api/track/{track_id}/stats?since={start_date}&until={end_date}",
            headers=headers,
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            stats = data.get("obj", {})
            
            # Extract Spotify streams
            spotify_data = stats.get("spotify", {})
            return {
                "total_streams": spotify_data.get("total_streams", 0),
                "daily_average": spotify_data.get("daily_average", 0),
                "popularity": spotify_data.get("popularity", 0),
                "has_data": True
            }
        else:
            print(f"      Stats endpoint returned {response.status_code}")
            return {"has_data": False}
            
    except Exception as e:
        print(f"      Could not fetch Spotify stats: {e}")
        return {"has_data": False}


async def ingest_cross_platform_data(db: Session):
    """
    Main ingestion with cross-platform data collection
    """
    print("=" * 70)
    print("🎵 ENHANCED DATA INGESTION - CROSS-PLATFORM TRENDING")
    print("   Collecting: TikTok Charts + Spotify Streaming Data")
    print("   Filter: Indie Labels & DistroKid Only")
    print("=" * 70)
    print()
    
    # Get Chartmetric token
    cm_client = get_chartmetric_client()
    await cm_client._ensure_token()
    token = cm_client._access_token
    
    if not token:
        print("❌ Failed to get Chartmetric token")
        return
    
    print(f"✅ Chartmetric authenticated\n")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch TikTok trending tracks
        print("📱 Fetching TikTok Charts...")
        tiktok_tracks = await fetch_tiktok_charts(client, token)
        print(f"   Found {len(tiktok_tracks)} TikTok tracks\n")
        
        print("🔍 Processing tracks with cross-platform data...\n")
        
        tracks_added = 0
        tracks_updated = 0
        tracks_skipped_major = 0
        tracks_skipped_no_label = 0
        
        for idx, track_data in enumerate(tiktok_tracks[:50]):  # Process top 50
            # Extract track info
            track_id = str(track_data.get("id") or track_data.get("cm_track"))
            track_name = track_data.get("name", "Unknown")
            artist_name = track_data.get("artist_names", "Unknown")
            
            if isinstance(artist_name, list):
                artist_name = ", ".join(artist_name)
            
            # Get label information
            label = None
            album_labels = track_data.get("album_label", [])
            if album_labels and isinstance(album_labels, list) and len(album_labels) > 0:
                label = album_labels[0]
            
            # Filter by label
            if not label:
                tracks_skipped_no_label += 1
                continue
            
            if not LabelDetector.should_include_for_discovery(label):
                classification, _ = LabelDetector.classify_label(label)
                tracks_skipped_major += 1
                continue
            
            # This is an indie track - fetch cross-platform data
            classification, _ = LabelDetector.classify_label(label)
            print(f"✅ Processing: {track_name} by {artist_name}")
            print(f"   Label: {label} ({classification})")
            
            # Check if track exists
            existing_track = db.query(Track).filter(Track.id == track_id).first()
            
            if not existing_track:
                # Create new track
                track = Track(
                    id=track_id,
                    title=track_name,
                    artist_name=artist_name,
                    spotify_id=track_data.get("spotify_id")
                )
                db.add(track)
                db.flush()
                tracks_added += 1
            else:
                tracks_updated += 1
            
            # Fetch Spotify streaming data
            print(f"   📊 Fetching Spotify streaming stats...")
            await asyncio.sleep(0.8)  # Rate limit
            spotify_stats = await fetch_spotify_track_stats(client, token, track_id, days=30)
            
            # Extract TikTok metrics
            tiktok_posts = track_data.get("posts", 0)
            tiktok_views = track_data.get("views", 0)
            tiktok_rank = track_data.get("rank", 999)
            
            # Extract Spotify metrics
            spotify_streams = spotify_stats.get("total_streams", 0) if spotify_stats.get("has_data") else 0
            spotify_daily_avg = spotify_stats.get("daily_average", 0) if spotify_stats.get("has_data") else 0
            
            print(f"   TikTok: {tiktok_posts:,} posts, Rank #{tiktok_rank}")
            if spotify_stats.get("has_data"):
                print(f"   Spotify: {spotify_streams:,} streams, {spotify_daily_avg:,}/day avg")
            else:
                print(f"   Spotify: No streaming data available")
            
            # Create metric entry
            metric = TrackMetric(
                track_id=track_id,
                timestamp=datetime.now(),
                # TikTok metrics
                tiktok_posts=tiktok_posts,
                tiktok_views=tiktok_views,
                tiktok_chart_position=tiktok_rank,
                # Spotify metrics
                spotify_streams=spotify_streams if spotify_streams > 0 else None,
                spotify_daily_listeners=spotify_daily_avg if spotify_daily_avg > 0 else None,
            )
            db.add(metric)
            
            # Commit every 5 tracks
            if idx % 5 == 4:
                db.commit()
            
            print()
        
        db.commit()
        
        print("\n" + "=" * 70)
        print("INGESTION SUMMARY")
        print("=" * 70)
        print(f"✅ New indie tracks added: {tracks_added}")
        print(f"🔄 Existing tracks updated: {tracks_updated}")
        print(f"❌ Major label tracks skipped: {tracks_skipped_major}")
        print(f"⚠️  No label info: {tracks_skipped_no_label}")
        print(f"\n📊 Total indie tracks with cross-platform data: {tracks_added + tracks_updated}")


async def main():
    """Run enhanced ingestion"""
    db = SessionLocal()
    
    try:
        await ingest_cross_platform_data(db)
        
        print("\n✅ Enhanced ingestion complete!")
        print("\n🌐 View results at: http://localhost:8000/dashboard/discover\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
