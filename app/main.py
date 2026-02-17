from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import logging
import time
import sys

from app.api import auth, discover, mail, contracts
from app.api.discovery import router as discovery_router
from app.api.discovery.tiktok_trending import router as tiktok_trending_router
from app.api.discovery.pinned_songs import router as pinned_songs_router
from app.api.discovery.creators import router as creators_router
from app.api.discovery.song_analytics import router as song_analytics_router

# Configure logging - force unbuffered output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

# Force unbuffered stdout/stderr
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="A&R Portal",
    version="0.1.0"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Daily data refresh scheduler
def refresh_tiktok_data():
    """Refresh TikTok trending data from Chartex API"""
    try:
        from app.api.discovery import tiktok_trending
        logger.info(f"🔄 Starting daily TikTok data refresh at {datetime.now()}")
        
        # Clear the cache to force fresh data fetch
        tiktok_trending._response_cache.clear()
        
        logger.info("✅ Cache cleared successfully. Fresh data will be fetched on next request.")
    except Exception as e:
        logger.error(f"❌ Error refreshing TikTok data: {str(e)}")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(
    refresh_tiktok_data, 
    'cron', 
    hour=0,  # Run at midnight (00:00)
    minute=0,
    name='daily_tiktok_refresh'
)

@app.on_event("startup")
def startup_event():
    """Start the scheduler on app startup"""
    # Initialize database tables
    try:
        from app.db.base import Base
        from app.db.session import engine
        from app.models.user import User
        from app.models.discovery import Track, TrackMetric, TrackScore, Shortlist, DiscoveryRun, PinnedSong
        
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
    
    # Clear cache on startup to ensure fresh data
    try:
        from app.api.discovery import tiktok_trending
        tiktok_trending._response_cache.clear()
        logger.info("🧹 Cleared TikTok data cache on startup")
    except Exception as e:
        logger.warning(f"⚠️  Could not clear cache on startup: {str(e)}")
    
    scheduler.start()
    logger.info("🚀 Background scheduler started. Daily refresh scheduled at 00:00")

@app.on_event("shutdown")
def shutdown_event():
    """Shutdown the scheduler on app shutdown"""
    scheduler.shutdown()
    logger.info("⛔ Background scheduler stopped")

# ------------------------
# CORS
# ------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------
# Request logging middleware
# ------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"➡️  {request.method} {request.url.path}{'?' + str(request.url.query) if request.url.query else ''}")
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(f"⬅️  {request.method} {request.url.path} → {response.status_code} ({duration:.2f}s)")
    return response

# ------------------------
# Static files
# ------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

# ------------------------
# Routers
# ------------------------
app.include_router(auth.router)
app.include_router(discover.router)  # Legacy discover endpoints (keep for backward compatibility)
app.include_router(discovery_router)  # New Chartmetric-based discovery system
app.include_router(tiktok_trending_router)  # TikTok trending with historical time series
app.include_router(pinned_songs_router)  # Admin control: manually pin songs
app.include_router(creators_router)  # TikTok creators/influencers
app.include_router(song_analytics_router)  # Detailed song analytics (TikTok + Spotify)
app.include_router(mail.router)
app.include_router(contracts.router)

# ------------------------
# Public routes
# ------------------------
@app.get("/")
def root():
    return FileResponse("static/login.html")

@app.get("/dashboard")
def dashboard(request: Request):
    # Preserve query parameters when redirecting
    query_params = str(request.url.query)
    redirect_url = "/static/dashboard/home.html"
    if query_params:
        redirect_url += f"?{query_params}"
    return RedirectResponse(url=redirect_url)

@app.get("/dashboard/discover")
def dashboard_discover():
    return FileResponse("static/dashboard/discover.html")

@app.get("/dashboard/outreach")
def dashboard_outreach():
    return FileResponse("static/dashboard/outreach.html")

@app.get("/dashboard/status")
def dashboard_status():
    return FileResponse("static/dashboard/status.html")

@app.get("/dashboard/contracts")
def dashboard_contracts():
    return FileResponse("static/dashboard/contracts.html")

@app.get("/dashboard/tiktok-trending")
def dashboard_tiktok_trending():
    return FileResponse("static/dashboard/tiktok-trending.html")

@app.get("/dashboard/song-analytics")
def dashboard_song_analytics():
    return FileResponse("static/dashboard/song-analytics.html")

@app.get("/dashboard/creator-analytics")
def dashboard_creator_analytics():
    return FileResponse("static/dashboard/creator-analytics.html")

@app.get("/health")
def health():
    return {"status": "ok"}
