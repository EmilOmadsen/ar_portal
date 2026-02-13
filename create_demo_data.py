"""
Create demo data for testing the discovery system
Populates database with sample tracks and metrics
"""
from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.discovery import Track, TrackMetric
from app.core.discovery.selectors import TrendingSelector, EvergreenSelector


def create_demo_tracks(db: Session):
    """Create sample tracks"""
    print("📊 Creating demo tracks...\n")
    
    demo_tracks = [
        {"id": "demo_001", "title": "Summer Nights", "artist_name": "Nordic Dreams", "spotify_id": "spotify_001"},
        {"id": "demo_002", "title": "Copenhagen Vibes", "artist_name": "Danish Wave", "spotify_id": "spotify_002"},
        {"id": "demo_003", "title": "Midnight Sun", "artist_name": "Scandinavian Soul", "spotify_id": "spotify_003"},
        {"id": "demo_004", "title": "Baltic Breeze", "artist_name": "Nordic Pulse", "spotify_id": "spotify_004"},
        {"id": "demo_005", "title": "Northern Lights", "artist_name": "Aurora Sound", "spotify_id": "spotify_005"},
    ]
    
    for track_data in demo_tracks:
        # Check if exists
        existing = db.query(Track).filter(Track.id == track_data["id"]).first()
        if not existing:
            track = Track(**track_data, first_discovered=datetime.utcnow() - timedelta(days=random.randint(30, 180)))
            db.add(track)
            print(f"  ✅ Created: {track.title} by {track.artist_name}")
    
    db.commit()
    return [t["id"] for t in demo_tracks]


def create_trending_metrics(db: Session, track_id: str):
    """Create metrics that show trending behavior"""
    print(f"  📈 Adding trending metrics for {track_id}...")
    
    # Create 30 days of data showing growth
    for days_ago in range(30, 0, -1):
        timestamp = datetime.utcnow() - timedelta(days=days_ago)
        
        # Exponential growth pattern
        growth_factor = (31 - days_ago) / 30
        base_streams = 10000
        streams = int(base_streams * (1 + growth_factor * 5))
        
        # TikTok posts growing rapidly
        tiktok_posts = int(100 * growth_factor * 3)
        tiktok_views = int(50000 * growth_factor * 4)
        
        metric = TrackMetric(
            track_id=track_id,
            timestamp=timestamp,
            spotify_streams=streams,
            spotify_streams_7d=int(streams * 7),
            spotify_streams_30d=int(streams * 30),
            spotify_playlist_count=int(50 * growth_factor),
            tiktok_posts=tiktok_posts,
            tiktok_posts_7d=int(tiktok_posts * 7),
            tiktok_posts_30d=int(tiktok_posts * 30),
            tiktok_views=tiktok_views,
            tiktok_views_7d=int(tiktok_views * 7),
            tiktok_views_30d=int(tiktok_views * 30)
        )
        db.add(metric)
    
    db.commit()


def create_evergreen_metrics(db: Session, track_id: str):
    """Create metrics that show evergreen behavior"""
    print(f"  🌲 Adding evergreen metrics for {track_id}...")
    
    # Create 180 days of consistent data
    base_streams = 25000
    for days_ago in range(180, 0, -1):
        timestamp = datetime.utcnow() - timedelta(days=days_ago)
        
        # Very stable streams with low variance
        variance = random.uniform(0.95, 1.05)
        streams = int(base_streams * variance)
        
        metric = TrackMetric(
            track_id=track_id,
            timestamp=timestamp,
            spotify_streams=streams,
            spotify_streams_7d=int(streams * 7),
            spotify_streams_30d=int(streams * 30),
            spotify_playlist_count=random.randint(80, 95),
            tiktok_posts=random.randint(10, 30),
            tiktok_views=random.randint(5000, 10000)
        )
        db.add(metric)
    
    db.commit()


def main():
    """Create demo data and run scoring"""
    print("=" * 60)
    print("🎬 CREATING DEMO DATA FOR DISCOVERY SYSTEM")
    print("=" * 60)
    print()
    
    db = SessionLocal()
    
    try:
        # Create tracks
        track_ids = create_demo_tracks(db)
        
        print("\n📊 Adding metrics...\n")
        
        # First 2 tracks: trending behavior
        for i in range(2):
            create_trending_metrics(db, track_ids[i])
        
        # Last 3 tracks: evergreen behavior
        for i in range(2, 5):
            create_evergreen_metrics(db, track_ids[i])
        
        print("\n🧮 Running scoring pipelines...\n")
        
        # Score all tracks
        trending_run = TrendingSelector.run_discovery_batch(db, track_ids)
        print(f"  ✅ Trending: {trending_run.tracks_updated}/{trending_run.tracks_processed} tracks scored")
        
        evergreen_run = EvergreenSelector.run_discovery_batch(db, track_ids)
        print(f"  ✅ Evergreen: {evergreen_run.tracks_updated}/{evergreen_run.tracks_processed} tracks scored")
        
        print("\n" + "=" * 60)
        print("✅ DEMO DATA CREATED SUCCESSFULLY!")
        print("=" * 60)
        print()
        print("🌐 Now visit: http://localhost:8000/dashboard/discover")
        print("   to see the discovery system in action!")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
