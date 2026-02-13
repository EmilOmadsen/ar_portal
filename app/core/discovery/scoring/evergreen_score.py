"""
Evergreen track scoring engine
Identifies tracks with stable, predictable long-term value
"""
from typing import Dict, Tuple
from sqlalchemy.orm import Session
from app.models.discovery import Track
from app.core.discovery.features import SpotifyFeatures, TemporalFeatures
from .weights import EVERGREEN_WEIGHTS, MIN_THRESHOLDS
import numpy as np


class EvergreenScorer:
    """
    Calculate evergreen scores for tracks
    Score range: 0-100 (higher = more evergreen/stable)
    
    Evergreen ≠ Viral
    Evergreen = Predictable cashflow, low variance, consistent presence
    """
    
    @staticmethod
    def calculate_score(
        track: Track,
        track_id: str,
        db: Session
    ) -> Tuple[float, Dict[str, float], bool]:
        """
        Calculate evergreen score with component breakdown
        
        Args:
            track: Track model instance
            track_id: Track identifier
            db: Database session
        
        Returns:
            Tuple of (total_score, components, passes_threshold)
        """
        components = {}
        
        # 1. Stream consistency (40%) - PRIMARY SIGNAL
        consistency = SpotifyFeatures.calculate_stream_consistency(
            track_id, db, lookback_days=180
        )
        components["stream_consistency"] = consistency
        
        # 2. Active months ratio (30%)
        active_ratio = SpotifyFeatures.calculate_active_months_ratio(
            track_id, db, lookback_days=365
        )
        components["active_months_ratio"] = active_ratio
        
        # 3. Low variance bonus (20%)
        # Extra reward for VERY stable tracks (CV < 0.2)
        if consistency > 0.8:  # Very consistent
            components["low_variance_bonus"] = 1.0
        elif consistency > 0.6:
            components["low_variance_bonus"] = 0.5
        else:
            components["low_variance_bonus"] = 0.0
        
        # 4. Chart persistence (10%)
        # Bonus for tracks that stay on charts long-term
        has_chart = SpotifyFeatures.has_chart_presence(track_id, db, lookback_days=180)
        components["chart_persistence"] = 1.0 if has_chart else 0.0
        
        # Calculate weighted sum
        total_score = 0.0
        for feature, weight in EVERGREEN_WEIGHTS.items():
            total_score += components.get(feature, 0.0) * weight
        
        # Scale to 0-100
        total_score *= 100
        
        # Check minimum thresholds
        passes_threshold = EvergreenScorer._check_thresholds(track_id, db)
        
        return total_score, components, passes_threshold
    
    @staticmethod
    def _check_thresholds(track_id: str, db: Session) -> bool:
        """
        Check if track meets minimum thresholds for evergreen
        
        Returns:
            True if all thresholds passed
        """
        from datetime import datetime, timedelta
        from app.models.discovery import TrackMetric
        
        # Must have sufficient historical data
        data_points = TemporalFeatures.get_data_points_count(track_id, db, lookback_days=365)
        if data_points < MIN_THRESHOLDS["evergreen_min_data_points"]:
            return False
        
        # Must have been active for minimum months
        active_ratio = SpotifyFeatures.calculate_active_months_ratio(track_id, db, lookback_days=365)
        expected_active = MIN_THRESHOLDS["evergreen_min_active_months"] / 12
        if active_ratio < expected_active:
            return False
        
        # Must have minimum average streams
        now = datetime.utcnow()
        metrics = db.query(TrackMetric).filter(
            TrackMetric.track_id == track_id,
            TrackMetric.timestamp >= now - timedelta(days=180),
            TrackMetric.spotify_streams.isnot(None)
        ).all()
        
        if metrics:
            avg_streams = np.mean([m.spotify_streams for m in metrics if m.spotify_streams])
            if avg_streams < MIN_THRESHOLDS["evergreen_min_avg_streams"]:
                return False
        else:
            return False
        
        return True
