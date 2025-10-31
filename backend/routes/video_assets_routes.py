"""
Роуты для работы с артефактами (скачивание) и кэшем видео.
"""
from fastapi import APIRouter, HTTPException
import logging

from .video_dependencies import video_service, video_cache_service, heygen_service


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/video", tags=["video"])


@router.post("/download/{video_id}")
async def download_video(video_id: str, output_path: str):
    try:
        success = await video_service.download_video(video_id, output_path)
        if success:
            return {"success": True, "message": f"Видео {video_id} успешно скачано в {output_path}"}
        else:
            raise HTTPException(status_code=500, detail="Ошибка при скачивании видео")
    except Exception as e:
        logger.error(f"Ошибка при скачивании видео {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_video_cache_stats():
    try:
        stats = video_cache_service.get_cache_stats()
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"Ошибка при получении статистики кэша: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voices")
async def get_available_voices():
    try:
        raw = heygen_service.get_available_voices()
        # Нормализуем под фронт: ожидается поле voices (массив)
        voices = []
        if isinstance(raw, dict):
            # HeyGen обычно кладёт список в raw["data"]
            voices = raw.get("data") or raw.get("voices") or []
        return {"success": True, "voices": voices}
    except Exception as e:
        logger.error(f"Ошибка при получении голосов HeyGen: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/avatars")
async def get_available_avatars():
    try:
        raw = heygen_service.get_available_avatars()
        # Нормализуем под фронт: ожидается поле avatars (массив)
        avatars = []
        if isinstance(raw, dict):
            avatars = raw.get("data") or raw.get("avatars") or []
        return {"success": True, "avatars": avatars}
    except Exception as e:
        logger.error(f"Ошибка при получении аватаров HeyGen: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cache/lesson/{course_id}/{module_number}/{lesson_index}")
async def delete_cached_video(course_id: int, module_number: int, lesson_index: int):
    try:
        success = video_cache_service.delete_video(course_id, module_number, lesson_index)
        if success:
            return {"success": True, "message": "Кэшированное видео удалено"}
        else:
            return {"success": False, "message": "Кэшированное видео не найдено"}
    except Exception as e:
        logger.error(f"Ошибка при удалении кэшированного видео: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


