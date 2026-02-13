"""
Ingest data from Chartex API
- Evergreens: 10k+ daily streams for past year
- Trending: TikTok, Spotify, and cross-platform
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.discovery import Track, TrackMetric
from app.core.discovery.chartex_client import get_chartex_client
from app.core.discovery.label_detection import should_include_for_discovery
import statistics


async def fetch_and_ingest_evergreens(min_daily_streams: int = 10000, days: int = 365):
    """
    Find evergreen tracks with consistent 10k+ daily streams
    """
    print("\n" + "="*70)
    print("🌲 DISCOVERING EVERGREEN TRACKS (10k+ daily streams)")
    print("="*70)
    
    client = get_chartex_client()
    db = SessionLocal()
    
    try:
        # Get trending tracks from multiple sources to analyze
        print("\n📊 Fetching tracks to analyze...")
        
        tiktok_tracks = await client.get_trending_tiktok(limit=100)
        spotify_tracks = await client.get_trending_spotify(limit=100, chart_type="top")
        
        all_tracks = tiktok_tracks + spotify_tracks
        print(f"   Found {len(all_tracks)} tracks to check")
        
        evergreens_found = 0
        checked_count = 0
        
        for track_data in all_tracks:
            checked_count += 1
            
            # Extract track info
            track_id = track_data.get("id")
            title = track_data.get("title", track_data.get("name", "Unknown"))
            artist = track_data.get("artist", "Unknown")
            spotify_id = track_data.get("spotify_id")
            
            print(f"\n[{checked_count}/{len(all_tracks)}] Checking: {title} - {artist}")
            
            # Check label
            label_info = await client.get_track_label_info(track_id)
            if label_info:
                label = label_info.get("label", "")
                if not should_include_for_discovery(label):
                    print(f"   ⏭️  Skipping: Major label ({label})")
                    continue
            
            # Get streaming history (past year)
            print(f"   📈 Fetching streaming history...")
            history = await client.get_track_streaming_history(track_id, platform="spotify", days=days)
            
            if not history or "daily_streams" not in history:
                print(f"   ⚠️  No streaming history available")
                continue
            
            daily_streams = history["daily_streams"]  # List of daily stream counts
            
            if len(daily_streams) < 30:  # Need at least 30 days of data
                print(f"   ⚠️  Insufficient data ({len(daily_streams)} days)")
                continue
            
            # Calculate average and consistency
            avg_daily = statistics.mean(daily_streams)
            std_dev = statistics.stdev(daily_streams) if len(daily_streams) > 1 else 0
            coefficient_of_variation = (std_dev / avg_daily) if avg_daily > 0 else 0
            
            print(f"   📊 Avg daily: {avg_daily:,.0f} streams")
            print(f"   📊 Consistency: {(1 - coefficient_of_variation) * 100:.1f}%")
            
            # Check if qualifies as evergreen
            if avg_daily >= min_daily_streams:
                print(f"   ✅ EVERGREEN! Adding to database...")
                
                # Create or update track
                track = db.query(Track).filter(Track.id == track_id).first()
                if not track:
                    track = Track(
                        id=track_id,
                        title=title,
                        artist_name=artist,
                        spotify_id=spotify_id
                    )
                    db.add(track)
                    db.flush()
                
                # Add multiple metrics (recent 30 days)
                for i, streams in enumerate(daily_streams[-30:]):
                    metric_date = datetime.now() - timedelta(days=30-i)
                    
                    metric = TrackMetric(
                        track_id=track.id,
                        timestamp=metric_date,
                        spotify_streams=streams
                    )
                    db.add(metric)
                
                evergreens_found += 1
                db.commit()
            else:
                print(f"   ⏭️  Below threshold ({avg_daily:,.0f} < {min_daily_streams:,.0f})")
            
            # Rate limiting
            await asyncio.sleep(0.5)
        
        print("\n" + "="*70)
        print(f"✅ Found {evergreens_found} evergreen tracks")
        print(f"📊 Checked {checked_count} total tracks")
        print("="*70)
        
    finally:
        db.close()


async def fetch_and_ingest_trending():
    """
    Find trending tracks on TikTok, Spotify, and cross-platform
    """
    print("\n" + "="*70)
    print("🔥 DISCOVERING TRENDING TRACKS")
    print("="*70)
    
    client = get_chartex_client()
    db = SessionLocal()
    
    try:
        # Get trending from both platforms
        print("\n📊 Fetching TikTok trending...")
        tiktok_tracks = await client.get_trending_tiktok(limit=50)
        print(f"   Found {len(tiktok_tracks)} TikTok trending tracks")
        
        print("\n📊 Fetching Spotify viral...")
        spotify_tracks = await client.get_trending_spotify(limit=50, chart_type="viral")
        print(f"   Found {len(spotify_tracks)} Spotify viral tracks")
        
        # Create lookup for cross-platform detection
        spotify_track_ids = {t.get("id"): t for t in spotify_tracks}
        tiktok_track_ids = {t.get("id"): t for t in tiktok_tracks}
        
        # Combine all unique tracks
        all_track_ids = set(spotify_track_ids.keys()) | set(tiktok_track_ids.keys())
        
        print(f"\n📊 Processing {len(all_track_ids)} unique tracks...")
        
        added_count = 0
        skipped_major = 0
        cross_platform_count = 0
        
        for track_id in all_track_ids:
            # Get track data from either source
            track_data = spotify_track_ids.get(track_id) or tiktok_track_ids.get(track_id)
            
            title = track_data.get("title", track_data.get("name", "Unknown"))
            artist = track_data.get("artist", "Unknown")
            spotify_id = track_data.get("spotify_id")
            
            print(f"\n   {title} - {artist}")
            
            # Check label
            label_info = await client.get_track_label_info(track_id)
            if label_info:
                label = label_info.get("label", "")
                if not should_include_for_discovery(label):
                    print(f"      ⏭️  Major label: {label}")
                    skipped_major += 1
                    continue
            
            # Determine platform presence
            on_tiktok = track_id in tiktok_track_ids
            on_spotify = track_id in spotify_track_ids
            is_cross_platform = on_tiktok and on_spotify
            
            if is_cross_platform:
                cross_platform_count += 1
                print(f"      🎯 CROSS-PLATFORM (TikTok + Spotify)")
            elif on_tiktok:
                print(f"      📱 TikTok trending")
            else:
                print(f"      🎵 Spotify viral")
            
            # Get detailed metrics
            tiktok_metrics = None
            spotify_streams = 0
            
            if on_tiktok:
                tiktok_metrics = await client.get_track_tiktok_metrics(track_id)
            
            if on_spotify:
                # Get recent streams
                history = await client.get_track_streaming_history(track_id, platform="spotify", days=7)
                if history and "daily_streams" in history:
                    spotify_streams = sum(history["daily_streams"])
            
            # Create or update track
            track = db.query(Track).filter(Track.id == track_id).first()
            if not track:
                track = Track(
                    id=track_id,
                    title=title,
                    artist_name=artist,
                    spotify_id=spotify_id
                )
                db.add(track)
                db.flush()
            
            # Add metric
            metric = TrackMetric(
                track_id=track.id,
                timestamp=datetime.now(),
                tiktok_posts=tiktok_metrics.get("posts") if tiktok_metrics else None,
                tiktok_views=tiktok_metrics.get("views") if tiktok_metrics else None,
                spotify_streams=spotify_streams if spotify_streams > 0 else None
            )
            db.add(metric)
            
            added_count += 1
            db.commit()
            
            # Rate limiting
            await asyncio.sleep(0.3)
        
        print("\n" + "="*70)
        print(f"✅ Added {added_count} trending tracks")
        print(f"🎯 Cross-platform: {cross_platform_count}")
        print(f"⏭️  Skipped {skipped_major} major label tracks")
        print("="*70)
        
    finally:
        db.close()


async def main():
    """Run both ingestion processes"""
    print("\n" + "="*70)
    print("🎵 CHARTEX DATA INGESTION")
    print("="*70)
    
    choice = input("\nWhat would you like to ingest?\n1. Trending tracks\n2. Evergreen tracks\n3. Both\n\nChoice (1-3): ")
    
    if choice == "1":
        await fetch_and_ingest_trending()
    elif choice == "2":
        await fetch_and_ingest_evergreens()
    elif choice == "3":
        await fetch_and_ingest_trending()
        await fetch_and_ingest_evergreens()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())
