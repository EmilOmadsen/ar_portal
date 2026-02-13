import requests
import json
from collections import Counter

headers = {
    'X-APP-ID': 'emil_elmTTqJc',
    'X-APP-TOKEN': '4lgvbHQ5cYN-F6O2yQLLw4N4LI3MxjLXtNoNhvqWyyY'
}

print("Fetching top 500 songs from Chartex API...")

all_labels = []
url = 'https://api.chartex.com/external/v1/songs/'
params = {
    'sort_by': 'tiktok_total_video_count',
    'limit': 50
}

page = 1
total_fetched = 0

while total_fetched < 500:
    print(f"\nPage {page}...")
    response = requests.get(url, headers=headers, params=params, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        items = data.get('data', {}).get('items', [])
        
        if not items:
            print("No more songs found")
            break
        
        for song in items:
            label = song.get('label_name', '')
            if label and label.strip().lower() != 'none':
                all_labels.append(label.strip())
        
        total_fetched += len(items)
        print(f"   Got {len(items)} songs (total: {total_fetched})")
        
        # Get next page URL
        next_url = data.get('data', {}).get('next')
        if not next_url:
            print("No more pages")
            break
        
        url = next_url
        params = {}  # Next URL already has params
        page += 1
    else:
        print(f"ERROR: {response.status_code}")
        break

label_counts = Counter(all_labels)

print(f'\n Analyzed {total_fetched} songs')
print(f' Found {len(label_counts)} unique labels\n')
print('=' * 100)
print('ALL LABELS (sorted by frequency - showing major label affiliations):\n')

for label, count in label_counts.most_common():
    label_lower = label.lower()
    is_major = False
    major_type = ""
    
    # Universal Music Group
    if any(x in label_lower for x in [
        'universal', 'republic', 'def jam', 'interscope', 'island', 
        'capitol', 'motown', 'ume', 'umg', 'polydor', 'decca', 
        'virgin emi', 'verve', 'blue note', 'mercury', 'geffen'
    ]):
        is_major = True
        major_type = "[UNIVERSAL]"
    
    # Sony Music Entertainment
    elif any(x in label_lower for x in [
        'sony', 'columbia', 'rca', 'epic', 'arista', 'jive', 
        'legacy', 'provident', 'volcano', 'okeh'
    ]):
        is_major = True
        major_type = "[SONY]"
    
    # Warner Music Group
    elif any(x in label_lower for x in [
        'warner', 'atlantic', 'elektra', 'parlophone', 'asylum', 
        'rhino', 'reprise', 'sire', 'nonesuch', 'fueled by ramen'
    ]):
        is_major = True
        major_type = "[WARNER]"
    
    # BMG
    elif 'bmg' in label_lower:
        is_major = True
        major_type = "[BMG]"
    
    if is_major:
        print(f'{count:4d}x  {major_type:13s} {label}')
    elif count >= 2:  # Only show indies that appear multiple times
        print(f'{count:4d}x  [INDIE]      {label}')

# Save full data
with open('all_labels_analyzed.json', 'w', encoding='utf-8') as f:
    json.dump({
        'total_songs': total_fetched,
        'unique_labels': len(label_counts),
        'labels': [{'name': label, 'count': count} for label, count in label_counts.most_common()]
    }, f, indent=2, ensure_ascii=False)

print(f'\n Saved to all_labels_analyzed.json')

# Print summary
print(f'\n{"="*100}')
print('SUMMARY OF MAJOR LABELS FOUND:')
print(f'{"="*100}\n')

universal_count = sum(count for label, count in label_counts.items() if any(x in label.lower() for x in ['universal', 'republic', 'def jam', 'interscope', 'island', 'capitol', 'motown', 'ume', 'umg', 'polydor', 'decca', 'virgin emi', 'verve', 'blue note', 'mercury', 'geffen']))
sony_count = sum(count for label, count in label_counts.items() if any(x in label.lower() for x in ['sony', 'columbia', 'rca', 'epic', 'arista', 'jive', 'legacy', 'provident', 'volcano', 'okeh']))
warner_count = sum(count for label, count in label_counts.items() if any(x in label.lower() for x in ['warner', 'atlantic', 'elektra', 'parlophone', 'asylum', 'rhino', 'reprise', 'sire', 'nonesuch', 'fueled by ramen']))
bmg_count = sum(count for label, count in label_counts.items() if 'bmg' in label.lower())

print(f'Universal Music Group: {universal_count} songs')
print(f'Sony Music Entertainment: {sony_count} songs')
print(f'Warner Music Group: {warner_count} songs')
print(f'BMG: {bmg_count} songs')
print(f'Independent/Other: {total_fetched - universal_count - sony_count - warner_count - bmg_count} songs')
