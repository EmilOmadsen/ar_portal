"""
Chartmetric module initialization
"""
from .client import ChartmetricClient, get_chartmetric_client
from .spotify import SpotifyChartmetric
from .tiktok import TikTokChartmetric
from .models import (
    ChartmetricTrack,
    SpotifyChartEntry,
    TikTokChartEntry,
    SpotifyStats,
    TikTokStats
)

__all__ = [
    "ChartmetricClient",
    "get_chartmetric_client",
    "SpotifyChartmetric",
    "TikTokChartmetric",
    "ChartmetricTrack",
    "SpotifyChartEntry",
    "TikTokChartEntry",
    "SpotifyStats",
    "TikTokStats",
]
