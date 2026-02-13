"""
Check what data we have in the database and display cross-platform status
"""
from app.db.session import SessionLocal
from app.models.discovery import Track, TrackMetric
from sqlalchemy import func

db = SessionLocal()

print("\n" + "="*70)
print("CURRENT DATABASE STATE")
print("="*70)

# Get all tracks with their metrics
tracks = db.query(Track).all()
print(f"\nTotal tracks: {len(tracks)}")

# Check metrics
metrics = db.query(TrackMetric).all()
print(f"Total metrics: {len(metrics)}")

# Sample some data
print("\n" + "="*70)
print("SAMPLE TRACKS & METRICS")
print("="*70)

for track in tracks[:5]:
    print(f"\n🎵 {track.title} - {track.artist_name}")
    print(f"   ID: {track.id}")
    print(f"   Spotify ID: {track.spotify_id}")
    
    # Get metrics
    track_metrics = db.query(TrackMetric).filter(TrackMetric.track_id == track.id).all()
    print(f"   Metrics count: {len(track_metrics)}")
    
    if track_metrics:
        m = track_metrics[0]
        print(f"   TikTok Posts: {m.tiktok_posts:,}" if m.tiktok_posts else "   TikTok Posts: None")
        print(f"   TikTok Views: {m.tiktok_views:,}" if m.tiktok_views else "   TikTok Views: None")
        print(f"   Spotify Streams: {m.spotify_streams:,}" if m.spotify_streams else "   Spotify Streams: None")

# Check if any track has both platforms
print("\n" + "="*70)
print("CROSS-PLATFORM STATUS")
print("="*70)

tiktok_only = db.query(TrackMetric).filter(
    TrackMetric.tiktok_posts.isnot(None),
    TrackMetric.spotify_streams.is_(None)
).count()

spotify_only = db.query(TrackMetric).filter(
    TrackMetric.tiktok_posts.is_(None),
    TrackMetric.spotify_streams.isnot(None)
).count()

both_platforms = db.query(TrackMetric).filter(
    TrackMetric.tiktok_posts.isnot(None),
    TrackMetric.spotify_streams.isnot(None)
).count()

print(f"TikTok only: {tiktok_only}")
print(f"Spotify only: {spotify_only}")
print(f"Both platforms: {both_platforms}")

db.close()
