"""
Clean database and remove major label/big artist tracks
"""
from app.db.session import SessionLocal
from app.models.discovery import Track, TrackMetric, TrackScore

# List of major artists to exclude (case-insensitive)
MAJOR_ARTISTS = [
    'megan thee stallion',
    'drake',
    'taylor swift',
    'ariana grande',
    'billie eilish',
    'the weeknd',
    'ed sheeran',
    'justin bieber',
    'dua lipa',
    'post malone',
    'olivia rodrigo',
    'bad bunny',
    'travis scott',
    'cardi b',
    'doja cat',
    'harry styles',
    'adele',
    'beyonce',
    'kanye west',
    'eminem',
    'rihanna',
    'bruno mars',
    'kendrick lamar',
    'j cole',
    'nicki minaj',
    'lil nas x',
    'sza',
    'future',
    '21 savage',
    'lil baby',
    'roddy ricch',
    'pop smoke',
    'juice wrld',
    'xxxtentacion',
    'lil uzi vert',
    'dababy',
    'tyler the creator',
    'frank ocean',
    'childish gambino',
]

def is_major_artist(artist_name: str) -> bool:
    """Check if artist is a major/well-known artist"""
    artist_lower = artist_name.lower()
    
    # Check against known major artists
    for major in MAJOR_ARTISTS:
        if major in artist_lower or artist_lower in major:
            return True
    
    return False

def clean_database():
    """Remove tracks from major artists and major labels"""
    print("\n" + "="*70)
    print("CLEANING DATABASE - REMOVING MAJOR ARTISTS")
    print("="*70)
    
    db = SessionLocal()
    
    try:
        # Get all tracks
        tracks = db.query(Track).all()
        print(f"\n📊 Found {len(tracks)} tracks in database")
        
        removed_count = 0
        kept_count = 0
        
        for track in tracks:
            should_remove = False
            reason = ""
            
            # Check if major artist
            if is_major_artist(track.artist_name):
                should_remove = True
                reason = "Major artist"
            
            if should_remove:
                print(f"❌ Removing: {track.title} - {track.artist_name} ({reason})")
                db.delete(track)
                removed_count += 1
            else:
                print(f"✅ Keeping: {track.title} - {track.artist_name}")
                kept_count += 1
        
        db.commit()
        
        print("\n" + "="*70)
        print(f"✅ Removed {removed_count} tracks from major artists")
        print(f"✅ Kept {kept_count} indie tracks")
        print("="*70)
        
    finally:
        db.close()

if __name__ == "__main__":
    response = input("This will delete major artist tracks from the database. Continue? (y/n): ")
    if response.lower() == 'y':
        clean_database()
        print("\n✨ Database cleaned! Refresh your browser to see results.")
    else:
        print("Cancelled")
