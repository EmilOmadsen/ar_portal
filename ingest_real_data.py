"""
Real Data Ingestion from Chartmetric
Filters for indie labels and DistroKid only
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.discovery import Track, TrackMetric, DiscoveryRun
from app.core.discovery.chartmetric import get_chartmetric_client
from app.core.discovery.label_detection import LabelDetector
from app.core.discovery.selectors import TrendingSelector, EvergreenSelector
import httpx


async def fetch_spotify_viral_charts(client, token: str, country: str = "global", date: str = None) -> list:
    """
    Fetch Spotify Viral charts
    """
    if not date:
        date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = await client.get(
            f"https://api.chartmetric.com/api/charts/spotify/viral/{country}/{date}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("obj", [])
        else:
            print(f"   ⚠️  Spotify charts returned {response.status_code}: {response.text[:100]}")
            return []
    except Exception as e:
        print(f"   ❌ Error fetching Spotify charts: {e}")
        return []


async def fetch_tiktok_charts(client, token: str, date: str = None) -> list:
    """
    Fetch TikTok trending tracks
    """
    if not date:
        date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    
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
            # The response contains tracks directly in 'obj' as a dict
            # Extract the track list - the obj might be a string or list
            obj = data.get("obj", [])
           
            if not obj:
                return []
            
            # If obj is already a list of tracks, return it
            if isinstance(obj, list):
                return obj
            
            # If obj is a dict, it might contain nested data
            if isinstance(obj, dict):
                # Try to find the tracks list in various places
                for key in ['tracks', 'data', 'items']:
                    if key in obj and isinstance(obj[key], list):
                        return obj[key]
                # If no nested list found, wrap the dict itself
                return [obj]
            
            return []
        else:
            print(f"   ⚠️  TikTok charts returned {response.status_code}")
            return []
    except Exception as e:
        print(f"   ❌ Error fetching TikTok charts: {e}")
        return []


async def get_track_details(client, token: str, track_id: str) -> dict:
    """
    Get detailed track information including label
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = await client.get(
            f"https://api.chartmetric.com/api/track/{track_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("obj", {})
        else:
            return {}
    except Exception as e:
        print(f"   ⚠️  Could not fetch details for track {track_id}")
        return {}


async def ingest_real_data(db: Session):
    """
    Main ingestion workflow with indie label filtering
    """
    print("=" * 60)
    print("🎵 REAL DATA INGESTION FROM CHARTMETRIC")
    print("   Filter: Indie Labels & DistroKid Only")
    print("=" * 60)
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
        all_tracks = []
        
        # Fetch Spotify Viral Charts
        print("📊 Fetching Spotify Viral Charts (Global)...")
        spotify_tracks = await fetch_spotify_viral_charts(client, token, "global")
        print(f"   Found {len(spotify_tracks)} tracks")
        all_tracks.extend([{**t, "source": "spotify_viral"} for t in spotify_tracks])
        
        await asyncio.sleep(2)  # Rate limit protection
        
        # Fetch TikTok Charts
        print("📱 Fetching TikTok Charts...")
        tiktok_tracks = await fetch_tiktok_charts(client, token)
        print(f"   Found {len(tiktok_tracks)} tracks")
        all_tracks.extend([{**t, "source": "tiktok"} for t in tiktok_tracks])
        
        print(f"\n📦 Total tracks fetched: {len(all_tracks)}")
        
        # Process tracks with label filtering
        print("\n🔍 Filtering for indie labels...\n")
        
        tracks_added = 0
        tracks_skipped_major = 0
        tracks_skipped_no_label = 0
        
        for idx, track_data in enumerate(all_tracks[:30]):  # Limit to avoid rate limits
            # Extract track info
            track_id = track_data.get("id") or track_data.get("cm_track")
            track_name = track_data.get("name") or track_data.get("track_name", "Unknown")
            artist_name = track_data.get("artist_names", track_data.get("artist_name", "Unknown"))
            
            if isinstance(artist_name, list):
                artist_name = ", ".join(artist_name)
            
            # Get label information - try multiple fields
            label = None
            details = {}  # Initialize to empty dict
            
            # Try album_label first (array in TikTok data)
            album_labels = track_data.get("album_label", [])
            if album_labels and isinstance(album_labels, list) and len(album_labels) > 0:
                label = album_labels[0]
            
            # Fallback to direct label field
            if not label:
                label = track_data.get("label") or track_data.get("record_label")
            
            # If still no label, try fetching details
            if not label:
                await asyncio.sleep(0.5)  # Rate limit
                details = await get_track_details(client, token, str(track_id))
                label = details.get("label") or details.get("record_label")
            
            # Filter by label
            if not label:
                print(f"⚠️  Skipped: {track_name} - No label info")
                tracks_skipped_no_label += 1
                continue
            
            if not LabelDetector.should_include_for_discovery(label):
                classification, _ = LabelDetector.classify_label(label)
                print(f"❌ Skipped: {track_name} - {label} ({classification})")
                tracks_skipped_major += 1
                continue
            
            # This is an indie track!
            classification, _ = LabelDetector.classify_label(label)
            print(f"✅ Adding: {track_name} by {artist_name}")
            print(f"   Label: {label} ({classification})")
            
            # Get Spotify ID
            spotify_id = track_data.get("spotify_id") or details.get("spotify_id")
            
            # Check if track exists
            existing_track = db.query(Track).filter(Track.id == str(track_id)).first()
            
            if not existing_track:
                # Create new track
                track = Track(
                    id=str(track_id),
                    title=track_name,
                    artist_name=artist_name,
                    spotify_id=spotify_id
                )
                db.add(track)
                db.flush()  # Get the ID
            
            # Add metric
            metric = TrackMetric(
                track_id=str(track_id),
                timestamp=datetime.utcnow(),
                spotify_streams=track_data.get("streams"),
                spotify_chart_position=track_data.get("position") or track_data.get("rank"),
                tiktok_posts=track_data.get("posts"),
                tiktok_views=track_data.get("views")
            )
            db.add(metric)
            
            tracks_added += 1
            
            if idx % 5 == 0 and idx > 0:
                db.commit()  # Periodic commits
        
        db.commit()
        
        print("\n" + "=" * 60)
        print("INGESTION SUMMARY")
        print("=" * 60)
        print(f"✅ Indie tracks added: {tracks_added}")
        print(f"❌ Major label tracks skipped: {tracks_skipped_major}")
        print(f"⚠️  No label info: {tracks_skipped_no_label}")
        
        # Run scoring if we have tracks
        if tracks_added > 0:
            print("\n🧮 Running discovery scoring...\n")
            
            track_ids = [t.id for t in db.query(Track).filter(Track.id.notlike('demo%')).all()]
            
            trending_run = TrendingSelector.run_discovery_batch(db, track_ids)
            print(f"✅ Trending scored: {trending_run.tracks_updated} tracks")
            
            evergreen_run = EvergreenSelector.run_discovery_batch(db, track_ids)
            print(f"✅ Evergreen scored: {evergreen_run.tracks_updated} tracks")


async def main():
    """Run ingestion"""
    db = SessionLocal()
    
    try:
        # Remove demo data first
        print("🗑️  Removing demo data...")
        db.query(TrackMetric).filter(TrackMetric.track_id.like('demo%')).delete(synchronize_session=False)
        db.query(Track).filter(Track.id.like('demo%')).delete(synchronize_session=False)
        db.commit()
        print("✅ Demo data removed\n")
        
        await ingest_real_data(db)
        
        print("\n✅ Ingestion complete!")
        print("\n🌐 View results at: http://localhost:8000/dashboard/discover\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
