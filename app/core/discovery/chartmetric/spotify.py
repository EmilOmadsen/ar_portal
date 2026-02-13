"""
Spotify-specific Chartmetric endpoints
"""
from typing import List, Optional
from datetime import datetime, timedelta
from .client import ChartmetricClient
from .models import SpotifyChartEntry, SpotifyStats


class SpotifyChartmetric:
    """
    Spotify data from Chartmetric API
    """
    
    def __init__(self, client: ChartmetricClient):
        self.client = client
    
    async def get_viral_charts(
        self,
        country: str = "DK",
        date: Optional[str] = None,
        limit: int = 50
    ) -> List[SpotifyChartEntry]:
        """
        Get Spotify Viral 50 chart
        
        Args:
            country: ISO 2-letter country code (DK, US, etc)
            date: Date in YYYY-MM-DD format (defaults to yesterday)
            limit: Number of entries to return
        """
        if date is None:
            date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        endpoint = f"/charts/spotify/viral/{country}/{date}"
        response = await self.client.get(endpoint)
        
        entries = []
        for item in response.get("obj", [])[:limit]:
            entries.append(SpotifyChartEntry(
                track_id=item.get("id"),
                track_name=item.get("name"),
                artist_names=[item.get("artist_names", "Unknown")],
                position=item.get("position", 0),
                streams=item.get("streams"),
                date=date,
                country=country
            ))
        
        return entries
    
    async def get_freshfind_charts(
        self,
        country: str = "DK",
        date: Optional[str] = None,
        limit: int = 50
    ) -> List[SpotifyChartEntry]:
        """
        Get Spotify Fresh Finds chart (new/emerging tracks)
        
        Args:
            country: ISO 2-letter country code
            date: Date in YYYY-MM-DD format
            limit: Number of entries
        """
        if date is None:
            date = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        endpoint = f"/charts/spotify/freshfind/{country}/{date}"
        response = await self.client.get(endpoint)
        
        entries = []
        for item in response.get("obj", [])[:limit]:
            entries.append(SpotifyChartEntry(
                track_id=item.get("id"),
                track_name=item.get("name"),
                artist_names=[item.get("artist_names", "Unknown")],
                position=item.get("position", 0),
                streams=item.get("streams"),
                date=date,
                country=country
            ))
        
        return entries
    
    async def get_track_stats(
        self,
        track_id: str,
        since: Optional[str] = None,
        until: Optional[str] = None
    ) -> List[SpotifyStats]:
        """
        Get Spotify streaming stats for a track
        
        Args:
            track_id: Chartmetric track ID
            since: Start date YYYY-MM-DD (max 365 days ago)
            until: End date YYYY-MM-DD (defaults to today)
        
        Returns:
            List of daily streaming stats
        """
        if until is None:
            until = datetime.utcnow().strftime("%Y-%m-%dd")
        
        if since is None:
            since = (datetime.utcnow() - timedelta(days=180)).strftime("%Y-%m-%d")
        
        endpoint = f"/track/{track_id}/stats"
        params = {
            "platform": "spotify",
            "type": "streams",
            "since": since,
            "until": until
        }
        
        response = await self.client.get(endpoint, params=params)
        
        stats = []
        for item in response.get("obj", []):
            stats.append(SpotifyStats(
                date=item.get("date"),
                streams=item.get("value", 0)
            ))
        
        return stats
    
    async def get_playlist_count(self, track_id: str) -> int:
        """
        Get number of Spotify playlists containing this track
        
        Args:
            track_id: Chartmetric track ID
        """
        endpoint = f"/track/{track_id}/playlists/spotify"
        response = await self.client.get(endpoint)
        
        playlists = response.get("obj", [])
        return len(playlists)
