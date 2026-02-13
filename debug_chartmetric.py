"""
Debug Chartmetric API responses to understand available data
"""
import asyncio
from app.core.discovery.chartmetric import get_chartmetric_client
import json


async def debug_track_data():
    """Debug what data is available for tracks"""
    client = get_chartmetric_client()
    
    # Get a sample track from database
    from app.db.session import SessionLocal
    from app.models.discovery import Track
    
    db = SessionLocal()
    track = db.query(Track).first()
    
    if not track:
        print("No tracks found in database")
        return
    
    print(f"\n📊 Debugging track: {track.title} by {track.artist_name}")
    print(f"   Chartmetric ID: {track.id}")
    print(f"   Spotify ID: {track.spotify_id}")
    
    # Refresh token
    await client._ensure_token()
    token = client._access_token
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Try different endpoints
    endpoints = [
        f"/api/track/{track.id}",
        f"/api/track/{track.id}/stats",
        f"/api/track/{track.id}/streaming/spotify",
        f"/api/track/spotify/{track.spotify_id}" if track.spotify_id else None,
    ]
    
    endpoints = [e for e in endpoints if e is not None]
    
    for endpoint in endpoints:
        print(f"\n{'='*70}")
        print(f"Endpoint: {endpoint}")
        print('='*70)
        
        try:
            # Use the client's get method
            data = await client.get(endpoint)
            print(f"Status: 200")
            print(json.dumps(data, indent=2)[:2000])  # First 2000 chars
                
        except Exception as e:
            print(f"Exception: {e}")
    
    db.close()


if __name__ == "__main__":
    asyncio.run(debug_track_data())
