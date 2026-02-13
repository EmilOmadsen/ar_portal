"""
Pydantic models for Chartmetric API responses
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChartmetricTrack(BaseModel):
    """Track from Chartmetric API"""
    id: str
    name: str
    artist_names: List[str]
    isrc: Optional[str] = None
    spotify_id: Optional[str] = None


class SpotifyChartEntry(BaseModel):
    """Entry from Spotify charts"""
    track_id: str
    track_name: str
    artist_names: List[str]
    position: int
    streams: Optional[int] = None
    date: str
    country: str


class TikTokChartEntry(BaseModel):
    """Entry from TikTok charts"""
    track_id: str
    track_name: str
    artist_names: List[str]
    position: int
    posts: Optional[int] = None
    views: Optional[int] = None
    date: str


class SpotifyStats(BaseModel):
    """Spotify streaming stats"""
    date: str
    streams: int


class TikTokStats(BaseModel):
    """TikTok usage stats"""
    date: str
    posts: int
    views: int
