"""
Temporal features (time-based patterns)
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.discovery import Track, TrackMetric


class TemporalFeatures:
    """
    Time-based feature extraction
    """
    
    @staticmethod
    def get_track_age_days(track: Track) -> int:
        """
        Get track age in days since first discovered
        """
        return (datetime.utcnow() - track.first_discovered).days
    
    @staticmethod
    def is_new_discovery(track: Track, threshold_days: int = 30) -> bool:
        """
        Check if track was recently discovered
        """
        age = TemporalFeatures.get_track_age_days(track)
        return age <= threshold_days
    
    @staticmethod
    def calculate_recency_score(
        track_id: str,
        db: Session
    ) -> float:
        """
        Score based on data freshness (0-1)
        Higher = more recent data available
        """
        latest = db.query(TrackMetric).filter(
            TrackMetric.track_id == track_id
        ).order_by(TrackMetric.timestamp.desc()).first()
        
        if not latest:
            return 0.0
        
        days_old = (datetime.utcnow() - latest.timestamp).days
        
        # Fresh data (< 1 day) = 1.0
        # Week old = 0.7
        # Month old = 0.3
        # > 2 months = 0.0
        if days_old <= 1:
            return 1.0
        elif days_old <= 7:
            return 0.9
        elif days_old <= 30:
            return 0.5
        elif days_old <= 60:
            return 0.2
        else:
            return 0.0
    
    @staticmethod
    def get_data_points_count(
        track_id: str,
        db: Session,
        lookback_days: int = 90
    ) -> int:
        """
        Count number of data points available
        More data = higher confidence in scores
        """
        since = datetime.utcnow() - timedelta(days=lookback_days)
        
        count = db.query(TrackMetric).filter(
            TrackMetric.track_id == track_id,
            TrackMetric.timestamp >= since
        ).count()
        
        return count
