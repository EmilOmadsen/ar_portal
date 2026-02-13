"""
Chartmetric API base client
Handles authentication and base requests
"""
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from app.core.config import settings


class ChartmetricClient:
    """
    Base Chartmetric API client
    Handles auth token refresh and HTTP requests
    """
    
    def __init__(self):
        self.base_url = settings.CHARTMETRIC_BASE_URL
        self.api_key = settings.CHARTMETRIC_API_KEY
        self.refresh_token = settings.CHARTMETRIC_REFRESH_TOKEN
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    async def _ensure_token(self):
        """Ensure we have a valid access token"""
        if self._access_token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at - timedelta(minutes=5):
                return  # Token still valid
        
        # Refresh token
        await self._refresh_access_token()
    
    async def _refresh_access_token(self):
        """
        Refresh access token using refresh token
        Chartmetric tokens expire after ~2 weeks
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/token",
                json={
                    "refreshtoken": self.refresh_token
                },
                headers={
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                # Chartmetric returns {success: true, token: "xxx"} or {obj: {token: "xxx"}}
                if "token" in data:
                    self._access_token = data["token"]
                elif "obj" in data and "token" in data["obj"]:
                    self._access_token = data["obj"]["token"]
                else:
                    raise Exception(f"Unexpected token response format: {data}")
                # Chartmetric tokens typically last 14 days
                self._token_expires_at = datetime.utcnow() + timedelta(days=13)
                print(f"✅ Chartmetric access token refreshed")
            else:
                raise Exception(f"Failed to refresh Chartmetric token: {response.status_code} - {response.text}")
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Chartmetric API
        """
        await self._ensure_token()
        
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(
                    f"Chartmetric API error: {response.status_code} - {response.text}"
                )
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """GET request"""
        return await self._request("GET", endpoint, params=params)
    
    async def post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """POST request"""
        return await self._request("POST", endpoint, json_data=json_data)


# Singleton instance
_client: Optional[ChartmetricClient] = None


def get_chartmetric_client() -> ChartmetricClient:
    """Get or create Chartmetric client singleton"""
    global _client
    if _client is None:
        _client = ChartmetricClient()
    return _client
