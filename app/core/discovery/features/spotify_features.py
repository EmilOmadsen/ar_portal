"""
Spotify feature extraction
Deterministic heuristics only - no ML
"""
from typing import List, Optional
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.discovery import Track, TrackMetric


class SpotifyFeatures:
    """
    Extract Spotify-based features for discovery scoring
    """
    
    @staticmethod
    def calculate_stream_consistency(
        track_id: str,
        db: Session,
        lookback_days: int = 180
    ) -> float:
        """
        Calculate streaming consistency (low variance = good for evergreen)
        
        Returns:
            Score 0-1 (higher = more consistent)
        """
        since = datetime.utcnow() - timedelta(days=lookback_days)
        
        metrics = db.query(TrackMetric).filter(
            TrackMetric.track_id == track_id,
            TrackMetric.timestamp >= since,
            TrackMetric.spotify_streams.isnot(None)
        ).order_by(TrackMetric.timestamp).all()
        
        if len(metrics) < 30:  # Need at least 30 days
            return 0.0
        
        streams = [m.spotify_streams for m in metrics if m.spotify_streams]
        if not streams or max(streams) == 0:
            return 0.0
        
        # Calculate coefficient of variation (CV)
        mean_streams = np.mean(streams)
        std_streams = np.std(streams)
        
        if mean_streams == 0:
            return 0.0
        
        cv = std_streams / mean_streams
        
        # Normalize: CV of 0 = perfect (score 1.0), CV > 1 = chaotic (score 0)
        consistency_score = max(0, 1 - cv)
        
        return min(1.0, consistency_score)
    
    @staticmethod
    def calculate_stream_growth(
        track_id: str,
        db: Session,
        short_period: int = 7,
        long_period: int = 30
    ) -> float:
        """
        Calculate stream growth velocity (good for trending)
        
        Returns:
            Growth ratio (e.g., 2.5 = 250% growth)
        """
        now = datetime.utcnow()
        
        # Get recent metrics
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
        
        if not recent.spotify_streams_7d or not baseline.spotify_streams_7d:
            return 0.0
        
        if baseline.spotify_streams_7d == 0:
            return 10.0 if recent.spotify_streams_7d > 0 else 0.0
        
        growth = recent.spotify_streams_7d / baseline.spotify_streams_7d
        return growth
    
    @staticmethod
    def calculate_active_months_ratio(
        track_id: str,
        db: Session,
        lookback_days: int = 365
    ) -> float:
        """
        Calculate what percentage of months had streaming activity
        
        Returns:
            Ratio 0-1 (e.g., 0.83 = active 10/12 months)
        """
        since = datetime.utcnow() - timedelta(days=lookback_days)
        
        metrics = db.query(TrackMetric).filter(
            TrackMetric.track_id == track_id,
            TrackMetric.timestamp >= since,
            TrackMetric.spotify_streams.isnot(None),
            TrackMetric.spotify_streams > 0
        ).all()
        
        if not metrics:
            return 0.0
        
        # Group by month
        active_months = set()
        for m in metrics:
            month_key = (m.timestamp.year, m.timestamp.month)
            active_months.add(month_key)
        
        expected_months = lookback_days / 30
        ratio = len(active_months) / expected_months
        
        return min(1.0, ratio)
    
    @staticmethod
    def calculate_playlist_growth(
        track_id: str,
        db: Session,
        period: int = 30
    ) -> float:
        """
        Calculate playlist addition rate (trending signal)
        
        Returns:
            Growth ratio
        """
        now = datetime.utcnow()
        
        recent = db.query(TrackMetric).filter(
            TrackMetric.track_id == track_id,
            TrackMetric.timestamp >= now - timedelta(days=7)
        ).order_by(TrackMetric.timestamp.desc()).first()
        
        baseline = db.query(TrackMetric).filter(
            TrackMetric.track_id == track_id,
            TrackMetric.timestamp >= now - timedelta(days=period),
            TrackMetric.timestamp < now - timedelta(days=7)
        ).order_by(TrackMetric.timestamp.desc()).first()
        
        if not recent or not baseline:
            return 0.0
        
        if not recent.spotify_playlist_count or not baseline.spotify_playlist_count:
            return 0.0
        
        if baseline.spotify_playlist_count == 0:
            return 5.0 if recent.spotify_playlist_count > 0 else 0.0
        
        growth = recent.spotify_playlist_count / baseline.spotify_playlist_count
        return growth
    
    @staticmethod
    def has_chart_presence(
        track_id: str,
        db: Session,
        lookback_days: int = 90
    ) -> bool:
        """
        Check if track has appeared on any Spotify charts recently
        """
        since = datetime.utcnow() - timedelta(days=lookback_days)
        
        chart_entry = db.query(TrackMetric).filter(
            TrackMetric.track_id == track_id,
            TrackMetric.timestamp >= since,
            TrackMetric.spotify_chart_position.isnot(None)
        ).first()
        
        return chart_entry is not None
