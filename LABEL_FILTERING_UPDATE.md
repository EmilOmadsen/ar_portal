# Label Filtering Update - Comprehensive Major Label Detection

## Analysis Summary

I analyzed the **top 500 songs** from the Chartex API to identify all major label patterns in real trending music data.

### Data Found:
- **Total songs analyzed:** 500
- **Unique labels found:** 350
- **Universal Music Group songs:** 57 (11.4%)
- **Sony Music Entertainment songs:** 66 (13.2%)
- **Warner Music Group songs:** 43 (8.6%)
- **BMG songs:** 1 (0.2%)
- **Independent/Other:** 333 (66.6%)

## Updated Label Filters

### Universal Music Group (57+ keywords)
Based on actual API data, the filter now catches:

**Core identifiers:**
- universal, umg, ume, umc

**Major UMG labels:**
- Island, Def Jam, Interscope, Republic, Capitol, Motown, Geffen
- EMI, Virgin EMI, Polydor, Decca, Mercury, Blue Note, Verve

**Regional UMG:**
- Universal Music GmbH (Germany)
- Universal Music AB (Sweden)
- Universal Music Romania
- Universal Music India
- Universal Music Canada
- Universal Music Denmark
- Universal Music Operations
- Universal Island Records
- Universal Studios
- Universal International

**UMG sub-labels:**
- Darkroom, KIDinaKORNER, Aftermath, Top Dawg Entertainment
- Creator Records, Portfolio Managing Events

**Phrases that indicate UMG:**
- "division of umg"
- "under exclusive license to universal"
- "umg recordings"
- "a universal music company"

### Sony Music Entertainment (45+ keywords)
**Core identifiers:**
- sony, sony music, sme

**Major Sony labels:**
- Columbia, RCA, Epic, Arista, Legacy, Jive

**Regional Sony:**
- Sony Music Entertainment UK
- Sony Music Entertainment India
- Sony Music Entertainment US Latin
- Sony Music Entertainment Sweden
- Sony Music Entertainment Italy
- Sony Music Entertainment Norway
- Sony Music Entertainment Brasil
- Sony Music Entertainment Canada
- Sony Music Entertainment France
- Sony Music Entertainment Netherlands

**Sony sub-labels:**
- Disruptor Records, Kemosabe, Monkey Puzzle Records
- FAX Records, Vested in Culture, B1 Recordings
- STMPD RCRDS, Kreatell Music, Hyper Focal

**Phrases that indicate Sony:**
- "division of sony"
- "under exclusive license to sony"
- "unit of sony music"

### Warner Music Group (42+ keywords)
**Core identifiers:**
- warner, wmg, wea, warner music

**Major Warner labels:**
- Atlantic, Elektra, Rhino, Parlophone, Asylum
- Reprise, Fueled by Ramen, Nonesuch

**Regional Warner:**
- Warner Music UK
- Warner Music Latina
- Warner Music France
- Warner Music Sweden
- Warner Music South Africa
- Warner Music Germany
- Warner Records

**Warner sub-labels:**
- 300 Entertainment, Bad Batch Records, Rec. 118
- Major Tom's, Night Street Records, Please Rewind
- Extensive Music AB, Dua Lipa Limited, Tips Music Limited
- Chocolate City

**Phrases that indicate Warner:**
- "a warner music group company"
- "division of atlantic"
- "under exclusive license to warner"
- "distributed by warner"

### Big Indie Labels (50+ keywords)
Added comprehensive indie label detection including:

**Big Indian labels:**
- Super Cassettes (T-Series)
- Zee Music Company
- Ishtar Music
- Tips Industries/Tips Music

**Major Western Indies:**
- XL Recordings
- Young Money/Cash Money
- Taylor Swift (self-release)
- Spinnin Records
- NCS (NoCopyrightSounds)

**Digital Distributors:**
- AWAL, Believe, Ditto, CD Baby
- DistroKid, TuneCore, Empire
- Kobalt, Merlin, INgrooves
- The Orchard, Stem, ONErpm
- Symphonic, Amuse, UnitedMasters
- Repost, Vydia, Spinnup, Bandcamp
- LANDR, RouteNote, ReverbNation

**Regional Indies:**
- Sharabi Films, Sweven Records
- Heera Media, Safa Islamic
- Jendex Records, Koo Koo TV
- White Paddy Mountain, Thirdzy
- PointHits, Ponchet, Archer Music
- Lotus Music, Kevin MacLeod
- FloyyMenor

## Real Examples from API

### Universal Songs Found:
1. **"Thats So True"** - Gracie Abrams, under exclusive license to Interscope Records, a division of UMG Recordings
2. **"Emergency"** - Time S.p.A., under exclusive license to Universal Music GmbH
3. Multiple songs from Republic Records, Def Jam, Capitol Records

### Sony Songs Found:
1. **"Can We Kiss Forever?"** - Columbia Records, a Division of Sony Music Entertainment
2. **"Laxed (Siren Beat)"** - Columbia Records, a Division of Sony Music Entertainment
3. **"All I Want for Christmas Is You"** - Sony Music Entertainment

### Warner Songs Found:
1. **"Perfect"** - Asylum Records UK, a division of Atlantic Records UK, a Warner Music Group company
2. Multiple songs from Atlantic Recording Corporation

## Implementation

**File Updated:** `app/api/discovery/tiktok_trending.py` (lines 125-230)

The filtering logic now:
1. Combines all label fields (label_name, distributor, record_label)
2. Searches for ANY of the 150+ keywords/phrases
3. Case-insensitive matching
4. Catches full label names and common phrases like "division of" or "exclusive license to"

## Testing

To test in the browser:
1. Navigate to the discover page: http://localhost:8000/dashboard/discover
2. Click "Universal" filter - should now show many more songs (not just 1)
3. Test Sony, Warner, BMG, Big Indie filters
4. Each should show appropriate songs with matching labels in the "Record Label" column

## Before vs After

**BEFORE:** Only 1 Universal song matched (very specific exact matches)
**AFTER:** ~11-13% of trending songs match Universal (comprehensive sublabel detection)

This brings the filtering in line with real-world music industry label distribution.
