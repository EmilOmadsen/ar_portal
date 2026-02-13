"""
Centralized weight configuration for scoring
All weights must sum to 1.0 per scoring mode
"""

# TRENDING SCORE WEIGHTS (0-100)
# Focus: Early momentum detection
TRENDING_WEIGHTS = {
    "tiktok_posts_velocity": 0.30,      # 30% - Primary signal
    "tiktok_views_velocity": 0.20,      # 20% - Supporting TikTok signal
    "spotify_stream_growth": 0.20,      # 20% - Spotify confirmation
    "playlist_growth": 0.15,            # 15% - Industry validation
    "cross_platform_boost": 0.10,       # 10% - Both platforms growing
    "chart_entry_bonus": 0.05,          # 5% - Chart appearance
}

# EVERGREEN SCORE WEIGHTS (0-100)
# Focus: Stable, predictable long-term value
EVERGREEN_WEIGHTS = {
    "stream_consistency": 0.40,         # 40% - Low variance (primary)
    "active_months_ratio": 0.30,        # 30% - Continuous presence
    "low_variance_bonus": 0.20,         # 20% - Very stable = bonus
    "chart_persistence": 0.10,          # 10% - Long chart life (optional)
}

# MINIMUM THRESHOLDS
# Tracks below these thresholds are filtered out
MIN_THRESHOLDS = {
    # Trending minimums
    "trending_min_tiktok_posts_7d": 50,
    "trending_min_spotify_streams_7d": 10000,
    "trending_min_data_points": 7,
    
    # Evergreen minimums
    "evergreen_min_active_months": 6,
    "evergreen_min_data_points": 90,
    "evergreen_min_avg_streams": 5000,
}

# NORMALIZATION BOUNDS
# Used to normalize raw feature values to 0-1 range
NORMALIZATION = {
    # Velocity normalization (growth ratios)
    "max_velocity": 10.0,          # 10x growth = max score
    "min_velocity": 1.0,           # No growth = min score
    
    # Consistency normalization
    "perfect_consistency": 0.0,    # CV = 0
    "poor_consistency": 1.0,       # CV = 1
}

def validate_weights():
    """Ensure all weight configurations sum to 1.0"""
    trending_sum = sum(TRENDING_WEIGHTS.values())
    evergreen_sum = sum(EVERGREEN_WEIGHTS.values())
    
    assert abs(trending_sum - 1.0) < 0.001, f"Trending weights sum to {trending_sum}, not 1.0"
    assert abs(evergreen_sum - 1.0) < 0.001, f"Evergreen weights sum to {evergreen_sum}, not 1.0"

# Validate on module load
validate_weights()
