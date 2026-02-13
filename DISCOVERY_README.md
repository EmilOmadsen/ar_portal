# Discovery System - Implementation Guide

## 🎯 Overview

The A&R Portal now includes a production-ready **Chartmetric-based discovery system** that identifies:

1. **Trending Tracks** - Early momentum detection
2. **Evergreen Tracks** - Stable, predictable long-term value

**Core Principles:**
- ✅ No ML (fully deterministic heuristics)
- ✅ 100% explainable to A&R humans
- ✅ Track-level focus (artists are secondary)
- ✅ Strict layer separation (API ≠ business logic)

---

## 📁 New Project Structure

```
app/
├── core/
│   └── discovery/
│       ├── chartmetric/          # Chartmetric API integration
│       │   ├── client.py         # Base API client with auth
│       │   ├── spotify.py        # Spotify-specific endpoints
│       │   ├── tiktok.py         # TikTok-specific endpoints
│       │   └── models.py         # Pydantic response models
│       │
│       ├── features/             # Feature extraction (deterministic)
│       │   ├── spotify_features.py
│       │   ├── tiktok_features.py
│       │   └── temporal.py
│       │
│       ├── scoring/              # Scoring engines
│       │   ├── weights.py        # Centralized weight config
│       │   ├── trending_score.py # Trending calculator
│       │   └── evergreen_score.py # Evergreen calculator
│       │
│       ├── selectors/            # Orchestration layer
│       │   ├── trending.py       # Trending pipeline
│       │   └── evergreen.py      # Evergreen pipeline
│       │
│       └── explainability.py    # Human-readable explanations
│
├── api/
│   └── discovery/                # New discovery API endpoints
│       ├── router.py             # Main router
│       ├── trending.py           # GET /api/discovery/trending
│       ├── evergreen.py          # GET /api/discovery/evergreen
│       ├── shortlists.py         # POST /api/discovery/shortlist
│       └── explain.py            # GET /api/discovery/explain/{track_id}
│
└── models/
    └── discovery.py              # Database models
        ├── Track                 # Track metadata
        ├── TrackMetric           # Time-series metrics (append-only)
        ├── TrackScore            # Computed scores (append-only)
        ├── Shortlist             # A&R manual curation
        └── DiscoveryRun          # Batch run auditing
```

---

## 🔧 Setup Instructions

### 1. Install Dependencies

All required packages are already in `requirements.txt`:
- `httpx` - Async HTTP client for Chartmetric
- `numpy` - Statistical calculations
- `pydantic` - Data validation

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Add Chartmetric credentials to your `.env` file:

```env
# Chartmetric API Configuration
CHARTMETRIC_API_KEY=your_api_key_here
CHARTMETRIC_REFRESH_TOKEN=your_refresh_token_here
CHARTMETRIC_BASE_URL=https://api.chartmetric.com/api
```

**How to get Chartmetric credentials:**
1. Sign up at https://chartmetric.com
2. Generate API key from dashboard
3. Use refresh token endpoint to get long-lived token

### 3. Initialize Database

Run the database initialization to create new tables:

```bash
python init_db.py
```

This creates:
- `tracks` - Track metadata
- `track_metrics` - Time-series data (append-only)
- `track_scores` - Computed scores with explanations
- `shortlists` - A&R curation lists
- `discovery_runs` - Batch execution auditing

### 4. Start the Server

```bash
uvicorn app.main:app --reload --port 8000
```

---

## 🌐 API Endpoints

### Discovery System

#### **GET /api/discovery/health**
Check system status

#### **GET /api/discovery/trending**
Get trending tracks with momentum

**Query Parameters:**
- `limit` (default: 50, max: 200) - Number of tracks
- `min_score` (default: 50.0) - Minimum trending score
- `platform` (optional) - Filter: `spotify` or `tiktok`
- `country` (optional) - ISO code: `DK`, `US`, etc.

**Response:**
```json
{
  "total": 25,
  "tracks": [
    {
      "track_id": "cm123",
      "title": "Song Name",
      "artist_name": "Artist Name",
      "trending_score": 87.5,
      "summary": "Strong momentum: TikTok posts growing 3.5x",
      "why_selected": [
        "TikTok posts growing 3.5x (7d vs 30d)",
        "Spotify streams up 2.1x in past week",
        "Growing on BOTH TikTok and Spotify (high confidence)"
      ],
      "risk_flags": [
        "Limited historical data (8 points)"
      ],
      "components": {
        "tiktok_posts_velocity": 0.83,
        "spotify_stream_growth": 0.52
      }
    }
  ]
}
```

#### **GET /api/discovery/evergreen**
Get stable, long-term value tracks

**Query Parameters:**
- `limit` (default: 50)
- `min_score` (default: 60.0)
- `min_months` (default: 6) - Minimum history required

**Response:** Similar to trending, with `evergreen_score` instead

#### **GET /api/discovery/explain/{track_id}**
Get detailed explanation for any track

Returns both trending and evergreen analysis with component breakdowns

#### **POST /api/discovery/shortlist**
Add track to A&R shortlist

**Body:**
```json
{
  "track_id": "cm123",
  "priority": 1,
  "notes": "Great TikTok momentum, reach out ASAP"
}
```

#### **GET /api/discovery/shortlist**
Get A&R shortlist with workflow tracking

**Query Parameters:**
- `status` - Filter: `new`, `contacted`, `interested`, `passed`, `signed`

---

## 🧮 Scoring Logic

### Trending Score (0-100)

**Weights:**
```python
tiktok_posts_velocity   30%  # Primary signal
tiktok_views_velocity   20%  # Supporting TikTok
spotify_stream_growth   20%  # Spotify confirmation
playlist_growth         15%  # Industry validation
cross_platform_boost    10%  # Both platforms growing
chart_entry_bonus        5%  # Chart appearance
```

**Minimum Thresholds:**
- TikTok posts (7d) ≥ 50
- Spotify streams (7d) ≥ 10,000
- Data points ≥ 7

**Philosophy:** Find tracks **early** while momentum is building

---

### Evergreen Score (0-100)

**Weights:**
```python
stream_consistency      40%  # Low variance (PRIMARY)
active_months_ratio     30%  # Continuous presence
low_variance_bonus      20%  # Very stable = extra points
chart_persistence       10%  # Long chart life
```

**Minimum Thresholds:**
- Active months ≥ 6
- Data points ≥ 90
- Average streams ≥ 5,000

**Philosophy:** Identify tracks with **predictable cashflow**, not viral spikes

---

## 🧠 Explainability

Every score includes:

1. **why_selected** - Human-readable reasons
2. **risk_flags** - Warnings/caveats
3. **components** - Breakdown of feature scores
4. **summary** - One-sentence description

**Example:**
```json
{
  "why_selected": [
    "TikTok posts growing 3.5x (7d vs 30d)",
    "Spotify streams up 2.1x in past week",
    "Growing on BOTH TikTok and Spotify"
  ],
  "risk_flags": [
    "Single-platform growth only (may not translate)",
    "Low Spotify streams"
  ]
}
```

**No black boxes. No "AI decided".**

---

## 🗄️ Database Design

### Key Principles

1. **Append-Only** - Never overwrite historical data
2. **Track-Centric** - Track is the primary entity
3. **Timestamped** - All metrics and scores are timestamped

### Data Flow

```
Chartmetric API
    ↓
TrackMetric (raw data, append-only)
    ↓
Feature Extraction (spotify_features.py, tiktok_features.py)
    ↓
Scoring (trending_score.py, evergreen_score.py)
    ↓
TrackScore (computed scores, append-only)
    ↓
API Response (trending.py, evergreen.py)
```

---

## 🚀 Next Steps

### Immediate (MVP)
1. ✅ Core system implemented
2. ⏳ Add data ingestion cron job (periodic Chartmetric pulls)
3. ⏳ Add data visualization to frontend

### Phase 2
- Batch scoring endpoints
- Historical trend analysis
- Export reports for A&R meetings
- Market concentration analysis (DK vs US, etc.)

### Phase 3
- Genre classification (if needed)
- Similar track recommendations
- Predictive modeling (if ML is approved)

---

## 🔍 Data Sources

**Chartmetric Endpoints Used:**

1. **Spotify:**
   - `/charts/spotify/viral/{country}/{date}`
   - `/charts/spotify/freshfind/{country}/{date}`
   - `/track/{id}/stats` (streams)
   - `/track/{id}/playlists/spotify`

2. **TikTok:**
   - `/charts/tiktok/{country}/{date}`
   - `/track/{id}/tiktok/stats` (posts, views)

**Note:** TikTok daily streams are NOT available via Chartmetric.

---

## 🛡️ Important Notes

1. **Legacy Endpoints Preserved**
   - Old `/api/discover/*` endpoints still work
   - New system uses `/api/discovery/*` (note the 'y')

2. **Authentication Required**
   - All discovery endpoints require JWT token
   - Use existing Microsoft OAuth or traditional login

3. **Rate Limiting**
   - Chartmetric has rate limits
   - Consider caching for production

4. **No ML**
   - Everything is deterministic
   - Easy to debug and explain
   - Can add ML later if needed

---

## 📚 Key Files

**Configuration:**
- [app/core/config.py](app/core/config.py) - Settings
- [app/core/discovery/scoring/weights.py](app/core/discovery/scoring/weights.py) - Score weights

**Scoring Logic:**
- [app/core/discovery/scoring/trending_score.py](app/core/discovery/scoring/trending_score.py)
- [app/core/discovery/scoring/evergreen_score.py](app/core/discovery/scoring/evergreen_score.py)

**API Endpoints:**
- [app/api/discovery/trending.py](app/api/discovery/trending.py)
- [app/api/discovery/evergreen.py](app/api/discovery/evergreen.py)

**Explainability:**
- [app/core/discovery/explainability.py](app/core/discovery/explainability.py)

---

## 🤝 Contributing

When modifying scoring logic:

1. Update weights in `scoring/weights.py`
2. Document reasoning in code comments
3. Test with real Chartmetric data
4. Ensure explainability remains human-readable

**Remember:** A&R humans must trust and understand every decision.

---

## 📞 Support

For questions about the discovery system:
- Check this README
- Review code comments in `app/core/discovery/`
- Refer to master prompt in project docs

**Husk: Discovery ≠ Charts. Discovery er logik, scoring, filtering og forklaring.**
