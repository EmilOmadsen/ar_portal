# Record Label Filtering - Comprehensive Label List

This document lists all major record labels and their sublabels/imprints that are used for filtering in the A&R Portal.

## Universal Music Group (Filter: "Universal")

Universal Music Group is the world's largest music company.

**Main Labels & Subsidiaries:**
- Universal Music Group (UMG)
- Island Records
- Def Jam Recordings
- Interscope Records
- Republic Records
- Capitol Records
- Motown Records
- Geffen Records
- EMI Records
- Virgin Records
- Polydor Records
- Decca Records
- Blue Note Records
- Verve Records
- Astralwerks
- Harvest Records
- Deutsche Grammophon
- Spinefarm Records

## Sony Music Entertainment (Filter: "Sony")

Sony Music Entertainment is one of the "Big Three" major music companies.

**Main Labels & Subsidiaries:**
- Sony Music
- Columbia Records
- RCA Records
- Epic Records
- Arista Records
- Legacy Recordings
- Jive Records
- J Records
- LaFace Records
- Zomba Group
- Syco Music
- Provident Label Group
- VEVO
- Day 1 Distribution
- Insanity Records
- Certified Classics
- Black Butter Records

## Warner Music Group (Filter: "Warner")

Warner Music Group is one of the "Big Three" major music companies.

**Main Labels & Subsidiaries:**
- Warner Music
- Atlantic Records
- Elektra Records
- Rhino Entertainment
- Roadrunner Records
- Fueled by Ramen
- Big Beat Records
- Erato Records
- Nonesuch Records
- Parlophone Records
- Reprise Records
- Sire Records
- Asylum Records
- East West Records
- London Recordings
- Maverick Records
- Tommy Boy Records
- WEA International
- Big Machine Records
- 300 Entertainment

## BMG Rights Management (Filter: "BMG")

BMG is the world's fourth-largest music publisher and a significant record label.

**Main Labels:**
- BMG Rights Management
- BMG Music

## Major Independent Labels & Distributors (Filter: "Big Indie Labels")

These are significant independent labels and digital distribution services.

**Distribution Services:**
- AWAL (Artists Without A Label)
- Believe Digital
- Ditto Music
- CD Baby
- DistroKid
- TuneCore
- EMPIRE Distribution
- Kobalt Music
- Merlin Network
- INgrooves
- The Orchard
- STEM
- ONErpm
- Symphonic Distribution
- Amuse
- UnitedMasters
- Repost Network
- VYDIA
- Spinnup
- Bandcamp
- LANDR
- Level Music
- IDOL
- Altafonte
- FiNeTUNES
- A2IM (American Association of Independent Music)

## Other / Unsigned (Filter: "Other / Unsigned")

This category includes:
- Self-released artists
- Truly independent artists
- DIY releases
- Artists with no label affiliation
- Small regional labels not part of major distribution
- Artists using keywords like "self", "independent", "unsigned", "DIY"
- Labels that don't match any major or major indie patterns

---

## How Filtering Works

The filtering system checks the `label_name` field from the Chartex API against these label lists:

1. **Case-insensitive matching**: All label names are converted to lowercase for comparison
2. **Partial string matching**: The system looks for label keywords anywhere in the label name
3. **Comprehensive checking**: Checks label, distributor, and record_label fields
4. **Priority matching**: Songs are categorized by their strongest label affiliation

### Examples

- "Columbia Records, a Division of Sony Music Entertainment" → **Sony**
- "Island Def Jam" → **Universal** (matches both Island and Def Jam)
- "Rhino Entertainment Company, a Warner Music Group Company" → **Warner**
- "Distributed by ONErpm" → **Big Indie Labels**
- "Thirdzy" (no major affiliation) → **Other / Unsigned**

---

## Usage in Portal

Users can filter songs by clicking these buttons:
- **All** - Show all songs regardless of label
- **Universal** - Show only Universal Music Group and sublabels
- **Sony** - Show only Sony Music Entertainment and sublabels
- **Warner** - Show only Warner Music Group and sublabels
- **BMG** - Show only BMG Rights Management
- **Big Indie Labels** - Show major independent distributors
- **Other / Unsigned** - Show self-released and small independent labels

This filtering helps A&R professionals quickly identify songs by their commercial backing and distribution strength.
