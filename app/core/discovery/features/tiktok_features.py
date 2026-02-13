"""
TikTok feature extraction
Deterministic heuristics only - no ML
"""
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.discovery import TrackMetric


class TikTokFeatures:
    """
    Extract TikTok-based features for discovery scoring
    """
    
    @staticmethod
    def calculate_posts_velocity(
        track_id: str,
        db: Session,
        short_period: int = 7,
        long_period: int = 30
    ) -> float:
        """
        Calculate TikTok posts growth velocity (strong trending signal)
        
        Returns:
            Growth ratio (e.g., 3.0 = 300% increase in posts)
        """
        now = datetime.utcnow()
        
        recent = db.query(TrackMetric).filter(
            TrackMetric.track_id == track_id,
            TrackMetric.timestamp >= now - timedelta(days=short_period)
        ).order_by(TrackMetric.timestamp.desc()).first()
        
        baseline = db.query(TrackMetric).filter(
            TrackMetric.track_id == track_id,
            TrackMetric.timestamp >= now - timedelta(days=long_period),
            TrackMetric.timestamp < now - timedelta(days=short_period)
        ).order_by(TrackMetric.timestamp.desc()).first()
        
        if not recent or not baseline:
            return 0.0
        
        if not recent.tiktok_posts_7d or not baseline.tiktok_posts_7d:
            return 0.0
        
        if baseline.tiktok_posts_7d == 0:
            return 10.0 if recent.tiktok_posts_7d > 0 else 0.0
        
        velocity = recent.tiktok_posts_7d / baseline.tiktok_posts_7d
        return velocity
    
    @staticmethod
    def calculate_views_velocity(
        track_id: str,
        db: Session,
        short_period: int = 7,
        long_period: int = 30
    ) -> float:
        """
        Calculate TikTok views growth velocity
        
        Returns:
            Growth ratio
        """
        now = datetime.utcnow()
        
        recent = db.query(TrackMetric).filter(
            TrackMetric.track_id == track_id,
            TrackMetric.timestamp >= now - timedelta(days=short_period)
        ).order_by(TrackMetric.timestamp.desc()).first()
        
        baseline = db.query(TrackMetric).filter(
            TrackMetric.track_id == track_id,
            TrackMetric.timestamp >= now - timedelta(days=long_period),
            TrackMetric.timestamp < now - timedelta(days=short_period)
        ).order_by(TrackMetric.timestamp.desc()).first()
        
        if not recent or not baseline:
            return 0.0
        
        if not recent.tiktok_views_7d or not baseline.tiktok_views_7d:
            return 0.0
        
        if baseline.tiktok_views_7d == 0:
            return 10.0 if recent.tiktok_views_7d > 0 else 0.0
        
        velocity = recent.tiktok_views_7d / baseline.tiktok_views_7d
        return velocity
    
    @staticmethod
    def has_tiktok_momentum(
        track_id: str,
        db: Session,
        threshold_posts_7d: int = 100
    ) -> bool:
        """
        Check if track has meaningful TikTok activity
        
        Args:
            track_id: Track identifier
            db: Database session
            threshold_posts_7d: Minimum posts in last 7 days
        
        Returns:
            True if track has momentum
        """
        now = datetime.utcnow()
        
        recent = db.query(TrackMetric).filter(
            TrackMetric.track_id == track_id,
            TrackMetric.timestamp >= now - timedelta(days=7)
        ).order_by(TrackMetric.timestamp.desc()).first()
        
        if not recent or not recent.tiktok_posts_7d:
            return False
        
        return recent.tiktok_posts_7d >= threshold_posts_7d
    
    @staticmethod
    def calculate_cross_platform_confirmation(
        track_id: str,
        db: Session
    ) -> bool:
        """
        Check if track is growing on BOTH TikTok and Spotify
        Strong signal for real momentum vs. platform-specific viral
        
        Returns:
            True if both platforms show growth
        """
        now = datetime.utcnow()
        
        # Get most recent metric
        recent = db.query(TrackMetric).filter(
            TrackMetric.track_id == track_id,
            TrackMetric.timestamp >= now - timedelta(days=7)
        ).order_by(TrackMetric.timestamp.desc()).first()
        
        baseline = db.query(TrackMetric).filter(
            TrackMetric.track_id == track_id,
            TrackMetric.timestamp >= now - timedelta(days=30),
            TrackMetric.timestamp < now - timedelta(days=7)
        ).order_by(TrackMetric.timestamp.desc()).first()
        
        if not recent or not baseline:
            return False
        
        # Check TikTok growth
        tiktok_growing = False
        if recent.tiktok_posts_7d and baseline.tiktok_posts_7d:
            if baseline.tiktok_posts_7d > 0:
                tiktok_growing = recent.tiktok_posts_7d > baseline.tiktok_posts_7d
        
        # Check Spotify growth
        spotify_growing = False
        if recent.spotify_streams_7d and baseline.spotify_streams_7d:
            if baseline.spotify_streams_7d > 0:
                spotify_growing = recent.spotify_streams_7d > baseline.spotify_streams_7d
        
        return tiktok_growing and spotify_growing
    
    @staticmethod
    def has_chart_entry(
        track_id: str,
        db: Session,
        lookback_days: int = 30
    ) -> bool:
        """
        Check if track has appeared on TikTok charts
        """
        since = datetime.utcnow() - timedelta(days=lookback_days)
        
        chart_entry = db.query(TrackMetric).filter(
            TrackMetric.track_id == track_id,
            TrackMetric.timestamp >= since,
            TrackMetric.tiktok_chart_position.isnot(None)
        ).first()
        
        return chart_entry is not None
