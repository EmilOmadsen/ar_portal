"""
Add new columns to tracks table for Spotify integration
"""
import sqlite3

# Connect to database
conn = sqlite3.connect('ar_portal.db')
cursor = conn.cursor()

print("\n" + "="*70)
print("ADDING NEW COLUMNS TO TRACKS TABLE")
print("="*70)

# List of columns to add
columns_to_add = [
    ("image_url", "TEXT"),
    ("spotify_url", "TEXT"),
    ("tiktok_url", "TEXT"),
    ("spotify_popularity", "INTEGER"),
]

for column_name, column_type in columns_to_add:
    try:
        cursor.execute(f"ALTER TABLE tracks ADD COLUMN {column_name} {column_type}")
        print(f"✅ Added column: {column_name} ({column_type})")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print(f"⏭️  Column already exists: {column_name}")
        else:
            print(f"❌ Error adding {column_name}: {e}")

conn.commit()
conn.close()

print("\n" + "="*70)
print("✅ Database migration complete!")
print("="*70)
print("\nRestart the server for changes to take effect.")
