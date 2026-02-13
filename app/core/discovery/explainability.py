"""
Explainability module - human-readable justifications
CRITICAL: Every discovery decision must be explainable to A&R humans
No black boxes. No "AI decided".
"""
from typing import List, Dict
from sqlalchemy.orm import Session
from app.models.discovery import Track
from app.core.discovery.features import SpotifyFeatures, TikTokFeatures, TemporalFeatures


class ExplainabilityEngine:
    """
    Generate human-readable explanations for track selections
    """
    
    @staticmethod
    def explain_trending(
        track: Track,
        track_id: str,
        components: Dict[str, float],
        db: Session
    ) -> Dict[str, List[str]]:
        """
        Generate explanation for why track is trending
        
        Args:
            track: Track model
            track_id: Track identifier
            components: Score components from TrendingScorer
            db: Database session
        
        Returns:
            Dict with 'why_selected' and 'risk_flags' lists
        """
        why_selected = []
        risk_flags = []
        
        # TikTok momentum explanations
        if components.get("tiktok_posts_velocity", 0) > 0.5:
            velocity = TikTokFeatures.calculate_posts_velocity(track_id, db)
            why_selected.append(
                f"TikTok posts growing {velocity:.1f}x (7d vs 30d)"
            )
        
        if components.get("tiktok_views_velocity", 0) > 0.5:
            velocity = TikTokFeatures.calculate_views_velocity(track_id, db)
            why_selected.append(
                f"TikTok views accelerating {velocity:.1f}x"
            )
        
        # Spotify growth explanations
        if components.get("spotify_stream_growth", 0) > 0.5:
            growth = SpotifyFeatures.calculate_stream_growth(track_id, db)
            why_selected.append(
                f"Spotify streams up {growth:.1f}x in past week"
            )
        
        if components.get("playlist_growth", 0) > 0.5:
            why_selected.append(
                "Adding to Spotify playlists rapidly"
            )
        
        # Cross-platform validation
        if components.get("cross_platform_boost", 0) == 1.0:
            why_selected.append(
                "Growing on BOTH TikTok and Spotify (high confidence)"
            )
        else:
            risk_flags.append(
                "Single-platform growth only (may not translate)"
            )
        
        # Chart validation
        if components.get("chart_entry_bonus", 0) == 1.0:
            why_selected.append("Appeared on TikTok or Spotify charts")
        
        # Risk assessments
        track_age = TemporalFeatures.get_track_age_days(track)
        if track_age < 7:
            risk_flags.append(
                f"Very new to system ({track_age} days) - limited data"
            )
        
        data_points = TemporalFeatures.get_data_points_count(track_id, db, lookback_days=30)
        if data_points < 15:
            risk_flags.append(
                f"Limited historical data ({data_points} points)"
            )
        
        # Warn if only one platform has data
        from datetime import datetime, timedelta
        from app.models.discovery import TrackMetric
        
        recent = db.query(TrackMetric).filter(
            TrackMetric.track_id == track_id,
            TrackMetric.timestamp >= datetime.utcnow() - timedelta(days=7)
        ).order_by(TrackMetric.timestamp.desc()).first()
        
        if recent:
            if not recent.tiktok_posts_7d or recent.tiktok_posts_7d < 50:
                risk_flags.append("Low/no TikTok presence")
            if not recent.spotify_streams_7d or recent.spotify_streams_7d < 10000:
                risk_flags.append("Low Spotify streams")
        
        return {
            "why_selected": why_selected,
            "risk_flags": risk_flags
        }
    
    @staticmethod
    def explain_evergreen(
        track: Track,
        track_id: str,
        components: Dict[str, float],
        db: Session
    ) -> Dict[str, List[str]]:
        """
        Generate explanation for why track is evergreen
        
        Args:
            track: Track model
            track_id: Track identifier
            components: Score components from EvergreenScorer
            db: Database session
        
        Returns:
            Dict with 'why_selected' and 'risk_flags' lists
        """
        why_selected = []
        risk_flags = []
        
        # Consistency explanations
        consistency = components.get("stream_consistency", 0)
        if consistency > 0.8:
            why_selected.append(
                f"Extremely consistent streams (CV score: {consistency:.2f})"
            )
        elif consistency > 0.6:
            why_selected.append(
                f"Stable streaming pattern (CV score: {consistency:.2f})"
            )
        else:
            risk_flags.append(
                f"Some variance in streams (CV score: {consistency:.2f})"
            )
        
        # Active months
        active_ratio = components.get("active_months_ratio", 0)
        if active_ratio > 0.9:
            months = int(active_ratio * 12)
            why_selected.append(
                f"Active {months}/12 months in past year"
            )
        elif active_ratio > 0.7:
            months = int(active_ratio * 12)
            why_selected.append(
                f"Consistent presence ({months}/12 months active)"
            )
        else:
            risk_flags.append(
                "Gaps in streaming activity"
            )
        
        # Bonus features
        if components.get("low_variance_bonus", 0) == 1.0:
            why_selected.append(
                "Very low variance - highly predictable cashflow"
            )
        
        if components.get("chart_persistence", 0) == 1.0:
            why_selected.append(
                "Long-term chart presence (180+ days)"
            )
        
        # Track age check
        track_age = TemporalFeatures.get_track_age_days(track)
        if track_age < 180:
            risk_flags.append(
                f"Relatively new ({track_age} days) - evergreen status unproven"
            )
        
        # Data quality check
        data_points = TemporalFeatures.get_data_points_count(track_id, db, lookback_days=365)
        if data_points < 180:
            risk_flags.append(
                f"Limited long-term data ({data_points} points)"
            )
        
        # Growth check (evergreen should be stable, not growing)
        growth = SpotifyFeatures.calculate_stream_growth(track_id, db)
        if growth > 3.0:
            risk_flags.append(
                "Currently experiencing viral growth - may destabilize"
            )
        elif growth < 0.7:
            risk_flags.append(
                "Declining streams - may be losing evergreen status"
            )
        
        return {
            "why_selected": why_selected,
            "risk_flags": risk_flags
        }
    
    @staticmethod
    def generate_summary(
        track: Track,
        trending_score: float,
        evergreen_score: float,
        mode: str,
        why_selected: List[str],
        risk_flags: List[str]
    ) -> str:
        """
        Generate a one-sentence summary for A&R dashboard
        
        Args:
            track: Track model
            trending_score: Trending score 0-100
            evergreen_score: Evergreen score 0-100
            mode: 'trending' or 'evergreen'
            why_selected: List of selection reasons
            risk_flags: List of warnings
        
        Returns:
            Human-readable summary string
        """
        if mode == "trending":
            if trending_score > 80:
                level = "Strong"
            elif trending_score > 60:
                level = "Moderate"
            else:
                level = "Emerging"
            
            summary = f"{level} momentum"
            if len(why_selected) > 0:
                summary += f": {why_selected[0]}"
        
        else:  # evergreen
            if evergreen_score > 80:
                level = "Highly stable"
            elif evergreen_score > 60:
                level = "Stable"
            else:
                level = "Moderately stable"
            
            summary = f"{level} evergreen track"
            if len(why_selected) > 0:
                summary += f" - {why_selected[0]}"
        
        return summary
