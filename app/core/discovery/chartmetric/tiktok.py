"""
TikTok-specific Chartmetric endpoints
"""
from typing import List, Optional
from datetime import datetime, timedelta
from .client import ChartmetricClient
from .models import TikTokChartEntry


class TikTokChartmetric:
    """
    TikTok data from Chartmetric API
    """
    
    def __init__(self, client: ChartmetricClient):
        self.client = client
    
    async def get_top_tracks(
        self,
        country: str = "DK",
        date: Optional[str] = None,
        limit: int = 50
    ) -> List[TikTokChartEntry]:
        """
        Get TikTok top tracks chart
        
        Args:
            country: ISO 2-letter country code (DK, US, etc)
            date: Date in YYYY-MM-DD format (defaults to yesterday)
            limit: Number of entries to return
        """
        if date is None:
            date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        endpoint = f"/charts/tiktok/{country}/{date}"
        response = await self.client.get(endpoint)
        
        entries = []
        for item in response.get("obj", [])[:limit]:
            entries.append(TikTokChartEntry(
                track_id=item.get("id"),
                track_name=item.get("name"),
                artist_names=[item.get("artist_name", "Unknown")],
                position=item.get("position", 0),
                posts=item.get("posts"),
                views=item.get("views"),
                date=date
            ))
        
        return entries
    
    async def get_track_stats(
        self,
        track_id: str,
        period: str = "30d"
    ) -> dict:
        """
        Get TikTok usage stats for a track
        
        NOTE: Chartmetric does NOT provide daily TikTok streams
        We can only get aggregated posts/views over periods
        
        Args:
            track_id: Chartmetric track ID
            period: Time period (7d, 30d)
        
        Returns:
            Dict with posts and views counts
        """
        endpoint = f"/track/{track_id}/tiktok/stats"
        params = {"period": period}
        
        try:
            response = await self.client.get(endpoint, params=params)
            stats = response.get("obj", {})
            
            return {
                "posts": stats.get("posts", 0),
                "views": stats.get("views", 0),
                "period": period
            }
        except Exception:
            # If endpoint doesn't exist, return zeros
            return {
                "posts": 0,
                "views": 0,
                "period": period
            }
