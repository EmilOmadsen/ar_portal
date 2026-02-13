from datetime import datetime
from num2words import num2words
from app.core.contracts.builder.artist_block import build_artists
from app.core.contracts.builder.options import build_marketing_fields, build_advance, build_milestone_advance
from app.core.contracts.builder.royalties import build_royalties


def build_context(payload: dict):
    """
    Build complete contract context following official CONTRACT LOGIC spec.
    Backend provides ONLY data - Word handles all text/layout/loops.
    """
    
    # ═══════════════════════════════════════════════════════
    # 1. PROJECT CODE: SUN{year}-R-{project_number}
    # ═══════════════════════════════════════════════════════
    year = payload.get('year', datetime.now().year)
    project_num = str(payload.get('project_number', '001')).zfill(3)
    project_code = f"SUN{year}-R-{project_num}"

    # ═══════════════════════════════════════════════════════
    # 2. ARTIST NAMES (for § 7.1 etc) - each name in quotes
    # ═══════════════════════════════════════════════════════
    artists_list = payload.get("artists", [])
    if len(artists_list) == 1:
        artist_names = f'"{artists_list[0].get("stage_name", "")}"'
    elif len(artists_list) == 2:
        artist_names = f'"{artists_list[0].get("stage_name", "")}" and "{artists_list[1].get("stage_name", "")}"'
    else:
        names = [f'"{a.get("stage_name", "")}"' for a in artists_list]
        artist_names = ", ".join(names[:-1]) + f", and {names[-1]}" if len(names) > 1 else ""

    # ═══════════════════════════════════════════════════════
    # 2.1 PUBLISHING ARTISTS (filtered by include_in_publishing toggle)
    # Only include artists who have publishing rights (if publishing is enabled)
    # ═══════════════════════════════════════════════════════
    publishing_included = payload.get("publishing_included", False)
    if publishing_included:
        # Filter artists who should appear in publishing agreement
        publishing_artists = [
            artist for artist in artists_list 
            if artist.get("include_in_publishing", True)  # Default True for backward compatibility
        ]
    else:
        # No publishing agreement - empty list
        publishing_artists = []

    # ═══════════════════════════════════════════════════════
    # 3. RECORDING COUNT AND TITLES
    # ═══════════════════════════════════════════════════════
    recordings = payload.get("recordings", [])
    recording_count = len(recordings) if recordings else 1
    recording_count_numeric = str(recording_count)
    recording_count_words = num2words(recording_count, lang='en').capitalize()
    
    # Format song titles
    if recordings:
        if len(recordings) == 1:
            song_titles = f'"{recordings[0]}"'
        elif len(recordings) == 2:
            song_titles = f'"{recordings[0]}" and "{recordings[1]}"'
        else:
            titles_list = [f'"{title}"' for title in recordings]
            song_titles = ", ".join(titles_list[:-1]) + f", and {titles_list[-1]}"
    else:
        song_titles = '"TBC"'

    # ═══════════════════════════════════════════════════════
    # 4. CONTRACT DATE (auto-filled with current date)
    # ═══════════════════════════════════════════════════════
    contract_date = datetime.now().strftime("%B %d, %Y")  # e.g., "January 19, 2026"
    
    return {
        # ─────────────────────────────
        # PROJECT IDENTIFICATION
        # ─────────────────────────────
        "project_code": project_code,
        "project_number": payload.get("project_number"),
        "year": year,
        "contract_date": contract_date,

        # ─────────────────────────────
        # ARTISTS (raw list - Word loops)
        # ─────────────────────────────
        "artists": build_artists(payload.get("artists", [])),
        
        # ─────────────────────────────
        # PUBLISHING ARTISTS (filtered by toggle - only if publishing enabled)
        # ─────────────────────────────
        "publishing_artists": build_artists(publishing_artists),
        
        # ─────────────────────────────
        # ARTIST NAMES (for single references in text)
        # ─────────────────────────────
        "artist_names": artist_names,

        # ─────────────────────────────
        # RECORDINGS
        # ─────────────────────────────
        "recording_count_numeric": recording_count_numeric,
        "recording_count_words": recording_count_words,
        "song_titles": song_titles,

        # ─────────────────────────────
        # ROYALTIES
        # ─────────────────────────────
        **build_royalties(payload),

        # ─────────────────────────────
        # PUBLISHING TOGGLE
        # ─────────────────────────────
        "publishing_included": payload.get("publishing_included", False),

        # ─────────────────────────────
        # MARKETING RECOUPMENT + OPTION
        # (numeric + words for all amounts)
        # ─────────────────────────────
        **build_marketing_fields(payload),

        # ─────────────────────────────
        # STANDARD ADVANCE
        # (numeric + words)
        # ─────────────────────────────
        **build_advance(payload),

        # ─────────────────────────────
        # MILESTONE ADVANCE
        # (numeric + words)
        # ─────────────────────────────
        **build_milestone_advance(payload),
    }
