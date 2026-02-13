"""
Chartex API Client
Access to TikTok song/sound data and trending charts
API Docs: https://chartex.com/apidocs
"""
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from app.core.config import settings


class ChartexClient:
    """
    Chartex API client for TikTok song and sound data
    """
    
    def __init__(self):
        self.base_url = "https://api.chartex.com"
        self.app_id = settings.CHARTEX_APP_ID
        self.app_token = settings.CHARTEX_APP_TOKEN
    
    def _get_headers(self, force_refresh: bool = False, mimic_browser: bool = True) -> Dict[str, str]:
        """Get authentication headers per Chartex API docs"""
        headers = {
            "X-APP-ID": self.app_id,
            "X-APP-TOKEN": self.app_token
        }
        
        # Add browser-like headers to match website requests
        if mimic_browser:
            headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            headers["Accept"] = "application/json, text/plain, */*"
            headers["Accept-Language"] = "en-US,en;q=0.9"
            headers["Referer"] = "https://chartex.com/"
        
        # Add cache-control headers to force fresh data from Chartex
        if force_refresh:
            headers["Cache-Control"] = "no-cache, no-store, max-age=0"
            headers["Pragma"] = "no-cache"
        return headers
    
    async def get_songs(
        self,
        limit: int = 50,
        sort_by: str = "tiktok_last_7_days_video_count",
        min_video_count: Optional[int] = None,
        search: Optional[str] = None,
        country_codes: Optional[str] = None,
        page: int = 1,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get songs from Chartex (TikTok data)
        
        sort_by options:
        - tiktok_total_video_count
        - tiktok_last_7_days_video_count (default)
        - tiktok_last_24_hours_video_count
        - tiktok_last_24_hours_video_percentage
        
        force_refresh: Add timestamp parameter to bypass Chartex caching
        """
        params = {
            "limit": limit,
            "sort_by": sort_by,
            "page": page,
            # Force latest data - try multiple parameter variations
            "latest": "true",
            "fresh": "true", 
            "cache": "false",
            "real_time": "true"
        }
        
        # Add cache-busting parameter with current timestamp
        params["_t"] = int(datetime.now().timestamp())
        
        if min_video_count:
            params["min_video_count"] = min_video_count
        if search:
            params["search"] = search
        if country_codes:
            params["country_codes"] = country_codes
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            print(f"\n📡 CHARTEX API REQUEST:")
            print(f"   URL: {self.base_url}/external/v1/songs/")
            print(f"   Params: {params}")
            print(f"   Time: {datetime.now()}")
            
            response = await client.get(
                f"{self.base_url}/external/v1/songs/",
                headers=self._get_headers(force_refresh=force_refresh),
                params=params
            )
            
            print(f"   Response Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                # Chartex API structure: { "data": { "items": [...] } }
                if "data" in data and "items" in data["data"]:
                    songs = data["data"]["items"]
                    print(f"   ✅ Got {len(songs)} songs from Chartex")
                    if songs:
                        print(f"   📊 First song: {songs[0].get('title', 'N/A')} by {songs[0].get('artist', 'N/A')}")
                        print(f"   📊 TikTok videos (24h): {songs[0].get('tiktok_last_24_hours_video_count', 0)}")
                        print(f"   📊 TikTok videos (7d): {songs[0].get('tiktok_last_7_days_video_count', 0)}")
                        print(f"   📊 TikTok videos (total): {songs[0].get('tiktok_total_video_count', 0)}")
                        
                        # Log first 3 songs to verify sort order
                        print(f"\n   🔍 Verifying sort order for '{sort_by}':")
                        for i, song in enumerate(songs[:3]):
                            sort_value = song.get(sort_by, 0)
                            print(f"      {i+1}. {song.get('title', 'N/A')}: {sort_value:,}")
                    return songs
                # Fallback for other structures
                return data.get("data", data.get("results", []))
            else:
                print(f"⚠️  Songs API error: {response.status_code} - {response.text}")
                return []
    
    async def get_song_detail(
        self,
        song_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific song
        """
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                f"{self.base_url}/external/v1/songs/{song_id}/",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️  Song detail error: {response.status_code}")
                return None
    
    async def get_tiktok_sounds(
        self,
        limit: int = 50,
        sort_by: str = "tiktok_last_7_days_video_count",
        search: Optional[str] = None,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get TikTok sounds/audio
        """
        params = {
            "limit": limit,
            "sort_by": sort_by,
            "page": page
        }
        
        if search:
            params["search"] = search
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                f"{self.base_url}/external/v1/tiktok-sounds/",
                headers=self._get_headers(),
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            else:
                print(f"⚠️  TikTok sounds error: {response.status_code}")
                return []
    
    async def get_song_stats(
        self,
        platform_id: str,
        platform: str,
        metric: str,
        mode: str = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit_by_latest_days: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get historical stats for a song on a specific platform
        
        Args:
            platform_id: TikTok sound ID (e.g., 7521377472742771478) or Spotify track ID (e.g., 4CgS09PVVpogWXX4VyDYJ3)
            platform: 'tiktok' or 'spotify'
            metric: 'spotify-streams', 'tiktok-video-views', or 'tiktok-video-counts'
            mode: 'daily' or 'total' (required)
            start_date: Filter start date (YYYY-MM-DD or YYYYMMDD)
            end_date: Filter end date (YYYY-MM-DD or YYYYMMDD)
            limit_by_latest_days: Limit to latest N days (e.g., 7, 30, 90)
        
        Returns:
            Dict with historical stats data or None if error
        """
        params = {
            "mode": mode
        }
        
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if limit_by_latest_days:
            params["limit_by_latest_days"] = limit_by_latest_days
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                f"{self.base_url}/external/v1/songs/{platform_id}/{platform}/stats/{metric}/",
                headers=self._get_headers(),
                params=params
            )
            
            print(f"🌐 Chartex API request: {self.base_url}/external/v1/songs/{platform_id}/{platform}/stats/{metric}/ with params: {params}")
            print(f"🌐 Status code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"🌐 Response structure: {list(result.keys()) if isinstance(result, dict) else type(result)}")
                return result
            else:
                print(f"⚠️  Song stats error: {response.status_code} for {platform_id}/{platform}/{metric}")
                print(f"⚠️  Response text: {response.text}")
                return None
    
    async def get_tiktok_sounds_for_song(
        self,
        spotify_id: str,
        sort_by: str = "tiktok_last_7_days_video_count",
        limit: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        Get TikTok sounds associated with a Spotify track
        
        Args:
            spotify_id: Spotify track ID
            sort_by: Field to sort by (default: tiktok_last_7_days_video_count)
            limit: Number of items per page (1-100, default: 1)
        
        Returns:
            Dict with TikTok sounds data or None if error
        """
        params = {
            "sort_by": sort_by,
            "limit": limit
        }
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                f"{self.base_url}/external/v1/songs/{spotify_id}/spotify/tiktok-sounds/",
                headers=self._get_headers(),
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️  TikTok sounds error: {response.status_code} for Spotify ID {spotify_id}")
                return None
    
    async def get_creators(
        self,
        limit: int = 20,
        sort_by: str = "total_followers",
        country_code: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get TikTok creators/influencers list
        
        Endpoint: /external/v1/accounts/
        """
        params = {
            "limit": limit,
            "sort_by": sort_by,
            "page": page,
            "_t": int(datetime.now().timestamp())
        }
        
        if country_code:
            params["country_code"] = country_code
        if search:
            params["search"] = search
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            print(f"📡 CHARTEX: GET /external/v1/accounts/ (page={page})")
            
            response = await client.get(
                f"{self.base_url}/external/v1/accounts/",
                headers=self._get_headers(force_refresh=force_refresh),
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("data", {}).get("items", [])
                print(f"✅ Got {len(items)} creators")
                return items
            else:
                print(f"❌ Creators API error: {response.status_code}")
                return []
    
    async def get_creator_metadata(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a TikTok creator
        
        Endpoint: /external/v1/accounts/{username}/metadata/
        """
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            print(f"📡 CHARTEX: GET /external/v1/accounts/{username}/metadata/")
            
            response = await client.get(
                f"{self.base_url}/external/v1/accounts/{username}/metadata/",
                headers=self._get_headers(force_refresh=True),
                params={"_t": int(datetime.now().timestamp())}
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Creator metadata error: {response.status_code}")
                return None
    
    async def get_creator_follower_stats(
        self,
        username: str,
        limit_by_latest_days: int = 30,
        mode: str = "daily"
    ) -> Optional[Dict[str, Any]]:
        """
        Get follower statistics for a TikTok creator
        
        Endpoint: /external/v1/accounts/{username}/stats/tiktok-follower-counts/
        """
        params = {
            "limit_by_latest_days": limit_by_latest_days,
            "mode": mode,
            "_t": int(datetime.now().timestamp())
        }
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            print(f"📡 CHARTEX: GET /external/v1/accounts/{username}/stats/tiktok-follower-counts/")
            
            response = await client.get(
                f"{self.base_url}/external/v1/accounts/{username}/stats/tiktok-follower-counts/",
                headers=self._get_headers(force_refresh=True),
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Creator follower stats error: {response.status_code}")
                return None
    
    async def get_creator_videos(
        self,
        username: str,
        limit: int = 20,
        sort_by: str = "tiktok_video_views",
        min_views: Optional[int] = None,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get videos from a TikTok creator
        
        Endpoint: /external/v1/accounts/{username}/video-statistics/
        """
        params = {
            "limit": limit,
            "sort_by": sort_by,
            "page": page,
            "_t": int(datetime.now().timestamp())
        }
        
        if min_views:
            params["tiktok_video_views"] = min_views
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            print(f"📡 CHARTEX: GET /external/v1/accounts/{username}/video-statistics/")
            
            response = await client.get(
                f"{self.base_url}/external/v1/accounts/{username}/video-statistics/",
                headers=self._get_headers(force_refresh=True),
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("data", {}).get("items", [])
                print(f"✅ Got {len(items)} videos from @{username}")
                return items
            else:
                print(f"❌ Creator videos error: {response.status_code}")
                return []
    
    async def get_song_stats(
        self,
        platform: str,
        platform_id: str,
        metric: str,
        limit_by_latest_days: int = 30,
        mode: str = "daily"
    ) -> Optional[Dict[str, Any]]:
        """
        Get historical stats for a song
        
        Endpoint: /external/v1/songs/{platform_id}/{platform}/stats/{metric}/
        Metrics: spotify-streams, tiktok-video-views, tiktok-video-counts
        """
        params = {
            "limit_by_latest_days": limit_by_latest_days,
            "mode": mode,
            "_t": int(datetime.now().timestamp())
        }
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            url = f"{self.base_url}/external/v1/songs/{platform_id}/{platform}/stats/{metric}/"
            print(f"📡 CHARTEX: GET {url}")
            
            response = await client.get(
                url,
                headers=self._get_headers(force_refresh=True),
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Song stats error: {response.status_code}")
                return None
    
    async def get_tiktok_sound_stats(
        self,
        tiktok_sound_id: str,
        metric: str,
        limit_by_latest_days: int = 30,
        mode: str = "daily"
    ) -> Optional[Dict[str, Any]]:
        """
        Get historical stats for a TikTok sound
        
        Endpoint: /external/v1/tiktok-sounds/{tiktok_sound_id}/stats/{metric}/
        Metrics: tiktok-video-counts, tiktok-video-views
        """
        params = {
            "limit_by_latest_days": limit_by_latest_days,
            "mode": mode,
            "_t": int(datetime.now().timestamp())
        }
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            url = f"{self.base_url}/external/v1/tiktok-sounds/{tiktok_sound_id}/stats/{metric}/"
            print(f"📡 CHARTEX: GET {url}")
            
            response = await client.get(
                url,
                headers=self._get_headers(force_refresh=True),
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ TikTok sound stats error: {response.status_code}")
                return None
    
    async def get_song_videos(
        self,
        platform: str,
        platform_id: str,
        limit: int = 20,
        sort_by: str = "tiktok_video_views",
        country_code: Optional[str] = None,
        time_range: str = "all_time",
        min_views: Optional[int] = None,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get TikTok videos using a song/sound
        
        Endpoint: /external/v1/songs/{platform_id}/{platform}/video-statistics/
        """
        params = {
            "limit": limit,
            "sort_by": sort_by,
            "time_range": time_range,
            "page": page,
            "_t": int(datetime.now().timestamp())
        }
        
        if country_code:
            params["country_code"] = country_code
        if min_views:
            params["tiktok_video_views"] = min_views
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            url = f"{self.base_url}/external/v1/songs/{platform_id}/{platform}/video-statistics/"
            print(f"📡 CHARTEX: GET {url}")
            
            response = await client.get(
                url,
                headers=self._get_headers(force_refresh=True),
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("data", {}).get("items", [])
                return items
            else:
                print(f"❌ Song videos error: {response.status_code}")
                return []
    
    async def get_song_influencers(
        self,
        platform: str,
        platform_id: str,
        limit: int = 20,
        sort_by: str = "sum_tiktok_video_total_views_by_username",
        country_code: Optional[str] = None,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get top influencers who used a song/sound
        
        Endpoint: /external/v1/songs/{platform_id}/{platform}/influencer-statistics/
        """
        params = {
            "limit": limit,
            "sort_by": sort_by,
            "page": page,
            "_t": int(datetime.now().timestamp())
        }
        
        if country_code:
            params["country_code"] = country_code
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            url = f"{self.base_url}/external/v1/songs/{platform_id}/{platform}/influencer-statistics/"
            print(f"📡 CHARTEX: GET {url}")
            
            response = await client.get(
                url,
                headers=self._get_headers(force_refresh=True),
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("data", {}).get("items", [])
                return items
            else:
                print(f"❌ Song influencers error: {response.status_code}")
                return []
    
    async def get_song_countries(
        self,
        platform: str,
        platform_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get country breakdown for a song/sound
        
        Endpoint: /external/v1/songs/{platform_id}/{platform}/country-statistics/
        """
        params = {
            "limit": limit,
            "_t": int(datetime.now().timestamp())
        }
        
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            url = f"{self.base_url}/external/v1/songs/{platform_id}/{platform}/country-statistics/"
            print(f"📡 CHARTEX: GET {url}")
            
            response = await client.get(
                url,
                headers=self._get_headers(force_refresh=True),
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("data", {}).get("items", [])
                return items
            else:
                print(f"❌ Song countries error: {response.status_code}")
                return []


# Singleton instance
_chartex_client: Optional[ChartexClient] = None


def get_chartex_client() -> ChartexClient:
    """Get or create Chartex client singleton"""
    global _chartex_client
    if _chartex_client is None:
        _chartex_client = ChartexClient()
    return _chartex_client
