"""
Enrich existing tracks with Spotify data (images, popularity, links)
Run this after adding Spotify credentials to .env
"""
import asyncio
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.discovery import Track
from app.core.discovery.spotify_client import get_spotify_client


def build_tiktok_url(tiktok_id: str) -> str:
    """Build TikTok sound URL from ID"""
    if tiktok_id:
        return f"https://www.tiktok.com/music/{tiktok_id}"
    return None


def build_spotify_url(spotify_id: str) -> str:
    """Build Spotify track URL from ID"""
    if spotify_id:
        return f"https://open.spotify.com/track/{spotify_id}"
    return None


async def enrich_track_with_spotify(db: Session, track: Track, spotify_client):
    """Enrich a single track with Spotify data"""
    
    # Build platform URLs
    if track.tiktok_id and not track.tiktok_url:
        track.tiktok_url = build_tiktok_url(track.tiktok_id)
    
    if track.spotify_id:
        if not track.spotify_url:
            track.spotify_url = build_spotify_url(track.spotify_id)
        
        # Get Spotify track data
        try:
            spotify_data = await spotify_client.get_track(track.spotify_id)
            
            if spotify_data:
                # Extract image URL (largest available)
                images = spotify_data.get("album", {}).get("images", [])
                if images:
                    track.image_url = images[0]["url"]  # First image is usually largest
                
                # Extract popularity
                track.spotify_popularity = spotify_data.get("popularity", 0)
                
                print(f"   ✅ Got Spotify data: popularity={track.spotify_popularity}, image={bool(track.image_url)}")
                return True
            else:
                print(f"   ⚠️  Track not found on Spotify")
                return False
                
        except Exception as e:
            print(f"   ❌ Error fetching Spotify data: {e}")
            return False
    else:
        # No Spotify ID - try searching
        print(f"   ⚠️  No Spotify ID, trying search...")
        try:
            result = await spotify_client.search_track(track.title, track.artist_name)
            if result:
                track.spotify_id = result["id"]
                track.spotify_url = result["external_urls"]["spotify"]
                track.spotify_popularity = result.get("popularity", 0)
                
                images = result.get("album", {}).get("images", [])
                if images:
                    track.image_url = images[0]["url"]
                
                print(f"   ✅ Found on Spotify: {track.spotify_id}, popularity={track.spotify_popularity}")
                return True
            else:
                print(f"   ⚠️  Not found on Spotify search")
                return False
        except Exception as e:
            print(f"   ❌ Search error: {e}")
            return False


async def enrich_all_tracks():
    """Enrich all tracks in database with Spotify data"""
    print("\n" + "="*70)
    print("🎵 ENRICHING TRACKS WITH SPOTIFY DATA")
    print("="*70)
    
    db = SessionLocal()
    spotify_client = get_spotify_client()
    
    try:
        # Get all tracks
        tracks = db.query(Track).all()
        print(f"\n📊 Found {len(tracks)} tracks to enrich\n")
        
        enriched_count = 0
        skipped_count = 0
        
        for i, track in enumerate(tracks, 1):
            print(f"[{i}/{len(tracks)}] {track.title} by {track.artist_name}")
            
            # Check if already enriched
            if track.image_url and track.spotify_popularity is not None:
                print(f"   ⏭️  Already enriched, skipping")
                skipped_count += 1
                continue
            
            success = await enrich_track_with_spotify(db, track, spotify_client)
            
            if success:
                enriched_count += 1
                db.commit()
            
            # Rate limiting - be nice to Spotify API
            await asyncio.sleep(0.1)
        
        print("\n" + "="*70)
        print(f"✅ Enriched {enriched_count} tracks")
        print(f"⏭️  Skipped {skipped_count} tracks (already enriched)")
        print("="*70)
        
    finally:
        db.close()


if __name__ == "__main__":
    print("\n⚠️  Make sure you have added SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET to your .env file")
    print("   Get them from: https://developer.spotify.com/dashboard\n")
    
    response = input("Continue? (y/n): ")
    if response.lower() == 'y':
        asyncio.run(enrich_all_tracks())
    else:
        print("Cancelled")
