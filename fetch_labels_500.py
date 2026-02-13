import requests
import json
from collections import Counter

headers = {
    'X-APP-ID': 'emil_elmTTqJc',
    'X-APP-TOKEN': '4lgvbHQ5cYN-F6O2yQLLw4N4LI3MxjLXtNoNhvqWyyY'
}

print("Fetching top 500 songs from Chartex API...")

all_labels = []
offset = 0
limit = 50
total_fetched = 0

while total_fetched < 500:
    print(f"\nFetching songs {total_fetched + 1} to {total_fetched + limit}...")
    response = requests.get(
        'https://api.chartex.com/external/v1/songs/',
        headers=headers,
        params={
            'sort_by': 'tiktok_total_video_count',
            'limit': limit,
            'offset': offset
        },
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        songs = data.get('data', [])
        
        if not songs:
            print("No more songs found")
            break
        
        for song in songs:
            label = song.get('label_name', '')
            if label and label.strip().lower() != 'none':
                all_labels.append(label.strip())
        
        total_fetched += len(songs)
        offset += limit
        print(f"   Got {len(songs)} songs (total: {total_fetched})")
    else:
        print(f"ERROR: {response.status_code}")
        break

label_counts = Counter(all_labels)

print(f'\n Analyzed {total_fetched} songs')
print(f' Found {len(label_counts)} unique labels\n')
print('=' * 80)
print('TOP 200 LABELS (sorted by frequency):\n')

for label, count in label_counts.most_common(200):
    print(f'{count:4d}x  {label}')

with open('all_labels_500.json', 'w', encoding='utf-8') as f:
    json.dump({
        'total_songs': total_fetched,
        'unique_labels': len(label_counts),
        'labels': [{'name': label, 'count': count} for label, count in label_counts.most_common()]
    }, f, indent=2, ensure_ascii=False)

print(f'\n Saved to all_labels_500.json')
