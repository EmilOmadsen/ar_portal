"""
Data Ingestion Script for Discovery System
Fetches data from Chartmetric and populates the database

Run this daily via cron job or scheduled task
"""
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.discovery import Track, TrackMetric, DiscoveryRun
from app.core.discovery.chartmetric import get_chartmetric_client, SpotifyChartmetric, TikTokChartmetric
from app.core.discovery.selectors import TrendingSelector, EvergreenSelector


async def ingest_spotify_charts(db: Session, country: str = "DK", limit: int = 50):
    """
    Ingest Spotify viral charts
    """
    print(f"📊 Fetching Spotify charts for {country}...")
    
    client = get_chartmetric_client()
    spotify = SpotifyChartmetric(client)
    
    try:
        # Get viral charts
        charts = await spotify.get_viral_charts(country=country, limit=limit)
        
        tracks_added = 0
        tracks_updated = 0
        
        for entry in charts:
            # Check if track exists
            track = db.query(Track).filter(Track.id == entry.track_id).first()
            
            if not track:
                # Create new track
                track = Track(
                    id=entry.track_id,
                    title=entry.track_name,
                    artist_name=", ".join(entry.artist_names),
                    spotify_id=entry.track_id
                )
                db.add(track)
                tracks_added += 1
                print(f"  ✅ Added: {track.title} by {track.artist_name}")
            else:
                tracks_updated += 1
            
            # Add metric data point
            metric = TrackMetric(
                track_id=entry.track_id,
                timestamp=datetime.utcnow(),
                spotify_streams=entry.streams,
                spotify_chart_position=entry.position,
                spotify_chart_country=entry.country
            )
            db.add(metric)
        
        db.commit()
        print(f"✅ Spotify: {tracks_added} new tracks, {tracks_updated} updated")
        return tracks_added, tracks_updated
        
    except Exception as e:
        print(f"❌ Error fetching Spotify charts: {e}")
        return 0, 0


async def ingest_tiktok_charts(db: Session, country: str = "DK", limit: int = 50):
    """
    Ingest TikTok top tracks
    """
    print(f"📱 Fetching TikTok charts for {country}...")
    
    client = get_chartmetric_client()
    tiktok = TikTokChartmetric(client)
    
    try:
        # Get TikTok charts
        charts = await tiktok.get_top_tracks(country=country, limit=limit)
        
        tracks_added = 0
        tracks_updated = 0
        
        for entry in charts:
            # Check if track exists
            track = db.query(Track).filter(Track.id == entry.track_id).first()
            
            if not track:
                # Create new track
                track = Track(
                    id=entry.track_id,
                    title=entry.track_name,
                    artist_name=", ".join(entry.artist_names),
                    tiktok_id=entry.track_id
                )
                db.add(track)
                tracks_added += 1
                print(f"  ✅ Added: {track.title} by {track.artist_name}")
            else:
                tracks_updated += 1
                
            # Add metric data point
            metric = TrackMetric(
                track_id=entry.track_id,
                timestamp=datetime.utcnow(),
                tiktok_posts=entry.posts,
                tiktok_views=entry.views,
                tiktok_chart_position=entry.position
            )
            db.add(metric)
        
        db.commit()
        print(f"✅ TikTok: {tracks_added} new tracks, {tracks_updated} updated")
        return tracks_added, tracks_updated
        
    except Exception as e:
        print(f"❌ Error fetching TikTok charts: {e}")
        return 0, 0


async def fetch_historical_data(db: Session, track_id: str, days: int = 30):
    """
    Fetch historical Spotify streaming data for a track
    Helps build up history for new tracks
    """
    client = get_chartmetric_client()
    spotify = SpotifyChartmetric(client)
    
    try:
        # Get historical stats
        until = datetime.utcnow().strftime("%Y-%m-%d")
        since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        stats = await spotify.get_track_stats(track_id, since=since, until=until)
        
        for stat in stats:
            # Check if we already have this data point
            existing = db.query(TrackMetric).filter(
                TrackMetric.track_id == track_id,
                TrackMetric.timestamp >= datetime.fromisoformat(stat.date),
                TrackMetric.timestamp < datetime.fromisoformat(stat.date) + timedelta(days=1)
            ).first()
            
            if not existing:
                metric = TrackMetric(
                    track_id=track_id,
                    timestamp=datetime.fromisoformat(stat.date),
                    spotify_streams=stat.streams
                )
                db.add(metric)
        
        db.commit()
        print(f"  📈 Added {len(stats)} historical data points for {track_id}")
        
    except Exception as e:
        print(f"  ⚠️  Could not fetch historical data for {track_id}: {e}")


async def run_scoring_pipelines(db: Session):
    """
    Run scoring on all tracks with sufficient data
    """
    print("\n🧮 Running scoring pipelines...")
    
    # Get all tracks
    tracks = db.query(Track).all()
    track_ids = [t.id for t in tracks]
    
    if not track_ids:
        print("  ⚠️  No tracks to score")
        return
    
    # Run trending scoring
    print(f"  📈 Scoring {len(track_ids)} tracks for trending...")
    trending_run = TrendingSelector.run_discovery_batch(db, track_ids)
    print(f"  ✅ Trending: {trending_run.tracks_updated} tracks scored")
    
    # Run evergreen scoring (only on tracks with enough history)
    print(f"  🌲 Scoring tracks for evergreen...")
    evergreen_run = EvergreenSelector.run_discovery_batch(db, track_ids)
    print(f"  ✅ Evergreen: {evergreen_run.tracks_updated} tracks scored")


async def main():
    """
    Main ingestion workflow
    """
    print("=" * 60)
    print("🚀 DISCOVERY SYSTEM DATA INGESTION")
    print("=" * 60)
    print(f"Started at: {datetime.utcnow().isoformat()}\n")
    
    db = SessionLocal()
    
    try:
        # Create discovery run record
        run = DiscoveryRun(
            run_type="ingestion",
            started_at=datetime.utcnow(),
            status="running"
        )
        db.add(run)
        db.commit()
        
        total_new = 0
        total_updated = 0
        
        # Ingest Spotify charts
        spotify_new, spotify_updated = await ingest_spotify_charts(db, country="DK", limit=50)
        total_new += spotify_new
        total_updated += spotify_updated
        
        # Ingest TikTok charts
        tiktok_new, tiktok_updated = await ingest_tiktok_charts(db, country="DK", limit=50)
        total_new += tiktok_new
        total_updated += tiktok_updated
        
        # Fetch historical data for new tracks (optional, takes time)
        print("\n📊 Fetching historical data for new tracks...")
        new_tracks = db.query(Track).order_by(Track.first_discovered.desc()).limit(10).all()
        for track in new_tracks:
            await fetch_historical_data(db, track.id, days=30)
        
        # Run scoring pipelines
        await run_scoring_pipelines(db)
        
        # Update run status
        run.completed_at = datetime.utcnow()
        run.status = "completed"
        run.tracks_new = total_new
        run.tracks_updated = total_updated
        run.tracks_processed = total_new + total_updated
        db.commit()
        
        print("\n" + "=" * 60)
        print("✅ INGESTION COMPLETE")
        print("=" * 60)
        print(f"New tracks: {total_new}")
        print(f"Updated tracks: {total_updated}")
        print(f"Completed at: {datetime.utcnow().isoformat()}")
        
    except Exception as e:
        print(f"\n❌ Error during ingestion: {e}")
        if 'run' in locals():
            run.status = "failed"
            run.error_message = str(e)
            db.commit()
    
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
