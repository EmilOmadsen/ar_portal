"""
Initialize database tables
"""
from app.db.base import Base
from app.db.session import engine
from app.models.user import User
from app.models.discovery import Track, TrackMetric, TrackScore, Shortlist, DiscoveryRun, PinnedSong

# Create all tables
Base.metadata.create_all(bind=engine)

print("✅ Database tables created successfully!")
print("   - users")
print("   - tracks")
print("   - track_metrics")
print("   - track_scores")
print("   - shortlists")
print("   - discovery_runs")
print("   - pinned_songs")
