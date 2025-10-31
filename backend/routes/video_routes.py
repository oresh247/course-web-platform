"""
API роуты для работы с HeyGen видео-генерацией (композит роутеров).
"""

from fastapi import APIRouter

from .video_generate_routes import router as generate_router
from .video_status_routes import router as status_router
from .video_assets_routes import router as assets_router


router = APIRouter()
router.include_router(generate_router)
router.include_router(status_router)
router.include_router(assets_router)
