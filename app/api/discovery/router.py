"""
Main discovery router
Coordinates all discovery endpoints
"""
from fastapi import APIRouter
from . import trending, evergreen, shortlists, explain

router = APIRouter(
    prefix="/api/discovery",
    tags=["discovery"]
)

# Include sub-routers
router.include_router(trending.router)
router.include_router(evergreen.router)
router.include_router(shortlists.router)
router.include_router(explain.router)


@router.get("/health")
async def discovery_health():
    """
    Check discovery system health
    """
    return {
        "status": "ok",
        "system": "discovery",
        "modes": ["trending", "evergreen"]
    }
