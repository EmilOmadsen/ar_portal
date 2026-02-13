"""
Discovery system data models
Track-level focus with historical metrics
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class Track(Base):
    """
    Core track entity - immutable metadata
    """
    __tablename__ = "tracks"

    id = Column(String, primary_key=True)  # Chartmetric track ID
    title = Column(String, nullable=False, index=True)
    artist_name = Column(String, nullable=False, index=True)
    isrc = Column(String, nullable=True, index=True)
    
    # Platform identifiers
    spotify_id = Column(String, nullable=True, index=True)
    tiktok_id = Column(String, nullable=True)
    
    # Media & Links
    image_url = Column(String, nullable=True)  # Album artwork URL
    spotify_url = Column(String, nullable=True)  # Direct Spotify link
    tiktok_url = Column(String, nullable=True)  # TikTok sound link
    
    # Spotify metadata
    spotify_popularity = Column(Integer, nullable=True)  # 0-100 popularity score
    
    # Discovery metadata
    first_discovered = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    metrics = relationship("TrackMetric", back_populates="track", cascade="all, delete-orphan")
    scores = relationship("TrackScore", back_populates="track", cascade="all, delete-orphan")
    shortlists = relationship("Shortlist", back_populates="track", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('ix_tracks_artist_title', 'artist_name', 'title'),
    )


class TrackMetric(Base):
    """
    Time-series metrics for tracks - APPEND ONLY
    Never overwrite, always create new records
    """
    __tablename__ = "track_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    track_id = Column(String, ForeignKey("tracks.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Spotify metrics
    spotify_streams = Column(Integer, nullable=True)
    spotify_streams_7d = Column(Integer, nullable=True)
    spotify_streams_30d = Column(Integer, nullable=True)
    spotify_playlist_count = Column(Integer, nullable=True)
    spotify_chart_position = Column(Integer, nullable=True)
    spotify_chart_country = Column(String, nullable=True)
    
    # TikTok metrics
    tiktok_posts = Column(Integer, nullable=True)
    tiktok_posts_7d = Column(Integer, nullable=True)
    tiktok_posts_30d = Column(Integer, nullable=True)
    tiktok_views = Column(Integer, nullable=True)
    tiktok_views_7d = Column(Integer, nullable=True)
    tiktok_views_30d = Column(Integer, nullable=True)
    tiktok_chart_position = Column(Integer, nullable=True)
    
    # Relationships
    track = relationship("Track", back_populates="metrics")
    
    __table_args__ = (
        Index('ix_track_metrics_track_timestamp', 'track_id', 'timestamp'),
    )


class TrackScore(Base):
    """
    Computed discovery scores - APPEND ONLY
    Each scoring run creates new records
    """
    __tablename__ = "track_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    track_id = Column(String, ForeignKey("tracks.id"), nullable=False, index=True)
    computed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Score types
    trending_score = Column(Float, nullable=True)  # 0-100
    evergreen_score = Column(Float, nullable=True)  # 0-100
    
    # Component scores (for debugging/explainability)
    components = Column(JSON, nullable=True)  # Dict of individual feature scores
    
    # Explainability
    why_selected = Column(JSON, nullable=True)  # List of reasons
    risk_flags = Column(JSON, nullable=True)  # List of warnings
    
    # Relationships
    track = relationship("Track", back_populates="scores")
    
    __table_args__ = (
        Index('ix_track_scores_trending', 'trending_score'),
        Index('ix_track_scores_evergreen', 'evergreen_score'),
        Index('ix_track_scores_track_computed', 'track_id', 'computed_at'),
    )


class Shortlist(Base):
    """
    Manual A&R shortlists - human curation
    """
    __tablename__ = "shortlists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    track_id = Column(String, ForeignKey("tracks.id"), nullable=False, index=True)
    
    # Who and when
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # A&R workflow
    status = Column(String, default="new", index=True)  # new, contacted, interested, passed, signed
    priority = Column(Integer, default=0)  # 0=normal, 1=high, 2=urgent
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Tracking
    contacted_at = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    track = relationship("Track", back_populates="shortlists")
    
    __table_args__ = (
        Index('ix_shortlists_status_priority', 'status', 'priority'),
        Index('ix_shortlists_user_added', 'user_id', 'added_at'),
    )


class DiscoveryRun(Base):
    """
    Track discovery execution runs for auditing
    """
    __tablename__ = "discovery_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_type = Column(String, nullable=False)  # trending, evergreen, ingestion
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Stats
    tracks_processed = Column(Integer, default=0)
    tracks_new = Column(Integer, default=0)
    tracks_updated = Column(Integer, default=0)
    
    # Status
    status = Column(String, default="running")  # running, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Metadata
    config = Column(JSON, nullable=True)  # Store run configuration
    
    __table_args__ = (
        Index('ix_discovery_runs_type_started', 'run_type', 'started_at'),
    )


class PinnedSong(Base):
    """
    Admin override system for manually pinning songs at the top of trending charts.
    Useful when API data doesn't match external sources.
    """
    __tablename__ = "pinned_songs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Song identification (matches Chartex API response)
    song_name = Column(String, nullable=False)
    artist_name = Column(String, nullable=False)
    spotify_id = Column(String, nullable=True)
    
    # Display metadata
    song_image_url = Column(String, nullable=True)
    label_name = Column(String, nullable=True)
    
    # Position
    pin_position = Column(Integer, nullable=False, unique=True)  # 1 = top, 2 = second, etc.
    
    # Admin control
    pinned_by = Column(String, nullable=True)  # Email of who pinned it
    pinned_at = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)  # Admin notes about why it's pinned
    
    # Status
    is_active = Column(Boolean, default=True)
