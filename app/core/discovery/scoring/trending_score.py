"""
Trending track scoring engine
Identifies tracks with early momentum
"""
from typing import Dict, Tuple
from sqlalchemy.orm import Session
from app.models.discovery import Track
from app.core.discovery.features import SpotifyFeatures, TikTokFeatures, TemporalFeatures
from .weights import TRENDING_WEIGHTS, MIN_THRESHOLDS, NORMALIZATION


class TrendingScorer:
    """
    Calculate trending scores for tracks
    Score range: 0-100 (higher = more trending)
    """
    
    @staticmethod
    def normalize_velocity(velocity: float) -> float:
        """
        Normalize velocity/growth ratio to 0-1 range
        
        Args:
            velocity: Growth ratio (e.g., 2.5 = 250% growth)
        
        Returns:
            Normalized score 0-1
        """
        min_vel = NORMALIZATION["min_velocity"]
        max_vel = NORMALIZATION["max_velocity"]
        
        if velocity <= min_vel:
            return 0.0
        elif velocity >= max_vel:
            return 1.0
        else:
            # Linear interpolation
            return (velocity - min_vel) / (max_vel - min_vel)
    
    @staticmethod
    def calculate_score(
        track: Track,
        track_id: str,
        db: Session
    ) -> Tuple[float, Dict[str, float], bool]:
        """
        Calculate trending score with component breakdown
        
        Args:
            track: Track model instance
            track_id: Track identifier
            db: Database session
        
        Returns:
            Tuple of (total_score, components, passes_threshold)
        """
        components = {}
        
        # 1. TikTok posts velocity (30%)
        tiktok_posts_vel = TikTokFeatures.calculate_posts_velocity(track_id, db)
        components["tiktok_posts_velocity"] = TrendingScorer.normalize_velocity(tiktok_posts_vel)
        
        # 2. TikTok views velocity (20%)
        tiktok_views_vel = TikTokFeatures.calculate_views_velocity(track_id, db)
        components["tiktok_views_velocity"] = TrendingScorer.normalize_velocity(tiktok_views_vel)
        
        # 3. Spotify stream growth (20%)
        spotify_growth = SpotifyFeatures.calculate_stream_growth(track_id, db)
        components["spotify_stream_growth"] = TrendingScorer.normalize_velocity(spotify_growth)
        
        # 4. Playlist growth (15%)
        playlist_growth = SpotifyFeatures.calculate_playlist_growth(track_id, db)
        components["playlist_growth"] = TrendingScorer.normalize_velocity(playlist_growth)
        
        # 5. Cross-platform boost (10%)
        cross_platform = TikTokFeatures.calculate_cross_platform_confirmation(track_id, db)
        components["cross_platform_boost"] = 1.0 if cross_platform else 0.0
        
        # 6. Chart entry bonus (5%)
        has_chart = (
            TikTokFeatures.has_chart_entry(track_id, db, lookback_days=30) or
            SpotifyFeatures.has_chart_presence(track_id, db, lookback_days=30)
        )
        components["chart_entry_bonus"] = 1.0 if has_chart else 0.0
        
        # Calculate weighted sum
        total_score = 0.0
        for feature, weight in TRENDING_WEIGHTS.items():
            total_score += components.get(feature, 0.0) * weight
        
        # Scale to 0-100
        total_score *= 100
        
        # Check minimum thresholds
        passes_threshold = TrendingScorer._check_thresholds(track_id, db)
        
        return total_score, components, passes_threshold
    
    @staticmethod
    def _check_thresholds(track_id: str, db: Session) -> bool:
        """
        Check if track meets minimum thresholds for trending
        
        Returns:
            True if all thresholds passed
        """
        from datetime import datetime, timedelta
        from app.models.discovery import TrackMetric
        
        # Get recent metrics
        now = datetime.utcnow()
        recent = db.query(TrackMetric).filter(
            TrackMetric.track_id == track_id,
            TrackMetric.timestamp >= now - timedelta(days=7)
        ).order_by(TrackMetric.timestamp.desc()).first()
        
        if not recent:
            return False
        
        # Check TikTok minimum
        if recent.tiktok_posts_7d:
            if recent.tiktok_posts_7d < MIN_THRESHOLDS["trending_min_tiktok_posts_7d"]:
                return False
        
        # Check Spotify minimum
        if recent.spotify_streams_7d:
            if recent.spotify_streams_7d < MIN_THRESHOLDS["trending_min_spotify_streams_7d"]:
                return False
        
        # Check data availability
        data_points = TemporalFeatures.get_data_points_count(track_id, db, lookback_days=30)
        if data_points < MIN_THRESHOLDS["trending_min_data_points"]:
            return False
        
        return True
