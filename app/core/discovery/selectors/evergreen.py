"""
Evergreen track selector
Orchestrates evergreen discovery pipeline
"""
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.discovery import Track, TrackScore, DiscoveryRun
from app.core.discovery.scoring import EvergreenScorer
from app.core.discovery.explainability import ExplainabilityEngine


class EvergreenSelector:
    """
    Select and score evergreen tracks
    Orchestrates the full evergreen discovery pipeline
    """
    
    @staticmethod
    def select_tracks(
        db: Session,
        limit: int = 50,
        min_score: float = 60.0,
        min_months: int = 6
    ) -> List[Dict]:
        """
        Select top evergreen tracks
        
        Args:
            db: Database session
            limit: Maximum number of tracks to return
            min_score: Minimum evergreen score threshold
            min_months: Minimum months of history required
        
        Returns:
            List of track dictionaries with scores and explanations
        """
        # Get all tracks with sufficient history
        from datetime import timedelta
        min_age = datetime.utcnow() - timedelta(days=min_months * 30)
        
        tracks = db.query(Track).filter(
            Track.first_discovered <= min_age
        ).all()
        
        scored_tracks = []
        
        for track in tracks:
            # Calculate score
            score, components, passes_threshold = EvergreenScorer.calculate_score(
                track, track.id, db
            )
            
            # Skip if below threshold
            if not passes_threshold or score < min_score:
                continue
            
            # Generate explanation
            explanation = ExplainabilityEngine.explain_evergreen(
                track, track.id, components, db
            )
            
            # Generate summary
            summary = ExplainabilityEngine.generate_summary(
                track, 0.0, score, "evergreen",
                explanation["why_selected"],
                explanation["risk_flags"]
            )
            
            scored_tracks.append({
                "track_id": track.id,
                "title": track.title,
                "artist_name": track.artist_name,
                "evergreen_score": round(score, 2),
                "components": {k: round(v, 3) for k, v in components.items()},
                "summary": summary,
                "why_selected": explanation["why_selected"],
                "risk_flags": explanation["risk_flags"],
                "first_discovered": track.first_discovered.isoformat(),
            })
        
        # Sort by score descending
        scored_tracks.sort(key=lambda x: x["evergreen_score"], reverse=True)
        
        # Limit results
        return scored_tracks[:limit]
    
    @staticmethod
    def score_and_persist(
        track: Track,
        track_id: str,
        db: Session
    ) -> Optional[TrackScore]:
        """
        Calculate evergreen score and persist to database
        
        Args:
            track: Track model instance
            track_id: Track identifier
            db: Database session
        
        Returns:
            TrackScore instance or None if below threshold
        """
        # Calculate score
        score, components, passes_threshold = EvergreenScorer.calculate_score(
            track, track_id, db
        )
        
        if not passes_threshold:
            return None
        
        # Generate explanation
        explanation = ExplainabilityEngine.explain_evergreen(
            track, track_id, components, db
        )
        
        # Check if we have a recent score record for this track
        existing_score = db.query(TrackScore).filter(
            TrackScore.track_id == track_id
        ).order_by(TrackScore.computed_at.desc()).first()
        
        # Create new score record (append-only)
        track_score = TrackScore(
            track_id=track_id,
            computed_at=datetime.utcnow(),
            evergreen_score=score,
            components={k: round(v, 4) for k, v in components.items()},
            why_selected=explanation["why_selected"],
            risk_flags=explanation["risk_flags"]
        )
        
        # If existing score exists, copy trending score
        if existing_score and existing_score.trending_score:
            track_score.trending_score = existing_score.trending_score
        
        db.add(track_score)
        db.commit()
        
        return track_score
    
    @staticmethod
    def run_discovery_batch(
        db: Session,
        track_ids: List[str]
    ) -> DiscoveryRun:
        """
        Run evergreen scoring on a batch of tracks
        
        Args:
            db: Database session
            track_ids: List of track IDs to score
        
        Returns:
            DiscoveryRun record with stats
        """
        run = DiscoveryRun(
            run_type="evergreen",
            started_at=datetime.utcnow(),
            status="running"
        )
        db.add(run)
        db.commit()
        
        tracks_processed = 0
        tracks_scored = 0
        
        try:
            for track_id in track_ids:
                track = db.query(Track).filter(Track.id == track_id).first()
                if not track:
                    continue
                
                tracks_processed += 1
                
                # Score and persist
                score = EvergreenSelector.score_and_persist(track, track_id, db)
                if score:
                    tracks_scored += 1
            
            # Update run status
            run.completed_at = datetime.utcnow()
            run.status = "completed"
            run.tracks_processed = tracks_processed
            run.tracks_updated = tracks_scored
            
        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
        
        db.commit()
        return run
