"""
Spotify Web API Client
Free tier provides track metadata, images, and popularity
"""
import httpx
import base64
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.config import settings


class SpotifyClient:
    """
    Spotify Web API client using Client Credentials flow
    https://developer.spotify.com/documentation/web-api/
    """
    
    def __init__(self):
        self.client_id = settings.SPOTIFY_CLIENT_ID
        self.client_secret = settings.SPOTIFY_CLIENT_SECRET
        self.base_url = "https://api.spotify.com/v1"
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    async def _ensure_token(self):
        """Ensure we have a valid access token"""
        if self._access_token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at - timedelta(minutes=5):
                return  # Token still valid
        
        await self._get_access_token()
    
    async def _get_access_token(self):
        """
        Get access token using Client Credentials flow
        https://developer.spotify.com/documentation/web-api/tutorials/client-credentials-flow
        """
        # Encode credentials
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://accounts.spotify.com/api/token",
                headers={
                    "Authorization": f"Basic {encoded}",
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                data={
                    "grant_type": "client_credentials"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self._access_token = data["access_token"]
                expires_in = data.get("expires_in", 3600)  # Usually 1 hour
                self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                print(f"✅ Spotify access token obtained")
            else:
                raise Exception(f"Failed to get Spotify token: {response.status_code} - {response.text}")
    
    async def get_track(self, spotify_id: str) -> Optional[Dict[str, Any]]:
        """
        Get track information including images and popularity
        https://developer.spotify.com/documentation/web-api/reference/get-track
        """
        await self._ensure_token()
        
        headers = {
            "Authorization": f"Bearer {self._access_token}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/tracks/{spotify_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None  # Track not found
            else:
                raise Exception(f"Spotify API error: {response.status_code} - {response.text}")
    
    async def get_track_audio_features(self, spotify_id: str) -> Optional[Dict[str, Any]]:
        """
        Get audio features (danceability, energy, etc.)
        https://developer.spotify.com/documentation/web-api/reference/get-audio-features
        """
        await self._ensure_token()
        
        headers = {
            "Authorization": f"Bearer {self._access_token}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/audio-features/{spotify_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                raise Exception(f"Spotify API error: {response.status_code} - {response.text}")
    
    async def search_track(self, title: str, artist: str) -> Optional[Dict[str, Any]]:
        """
        Search for a track by title and artist
        Returns the first match if found
        """
        await self._ensure_token()
        
        # Build search query
        query = f"track:{title} artist:{artist}"
        
        headers = {
            "Authorization": f"Bearer {self._access_token}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/search",
                headers=headers,
                params={
                    "q": query,
                    "type": "track",
                    "limit": 1
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                tracks = data.get("tracks", {}).get("items", [])
                return tracks[0] if tracks else None
            else:
                raise Exception(f"Spotify API error: {response.status_code} - {response.text}")


# Singleton instance
_spotify_client: Optional[SpotifyClient] = None


def get_spotify_client() -> SpotifyClient:
    """Get or create Spotify client singleton"""
    global _spotify_client
    if _spotify_client is None:
        _spotify_client = SpotifyClient()
    return _spotify_client
