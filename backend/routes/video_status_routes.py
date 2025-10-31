"""
Роуты статусов и диагностики видео.
"""
from fastapi import APIRouter, HTTPException
from typing import List
import logging
from datetime import datetime

from .video_dependencies import video_service, video_cache_service
from ..database import db


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/video", tags=["video"])


@router.get("/status/{video_id}")
async def get_video_status(video_id: str):
    try:
        status = await video_service.check_video_status(video_id)
        if status:
            video_status = status.get("status", "unknown")
            download_url = status.get("download_url")
            if video_status == "completed" and not download_url:
                download_url = f"https://resource2.heygen.ai/video/transcode/{video_id}/1280x720.mp4"
                logger.info(
                    f"✅ Сгенерирован URL для скачивания видео {video_id}: {download_url}"
                )
                status["download_url"] = download_url
            video_cache_service.update_video_status(
                video_id=video_id,
                status=video_status,
                download_url=download_url,
                duration=status.get("duration"),
                file_size=status.get("file_size"),
                error_message=status.get("error"),
                error_code=status.get("error_code"),
            )
            if video_status == "completed" and download_url:
                cached_video = video_cache_service.get_video_by_id(video_id)
                if cached_video:
                    parts = cached_video.lesson_key.split("_")
                    if len(parts) == 3:
                        try:
                            course_id = int(parts[0])
                            module_number = int(parts[1])
                            lesson_index = int(parts[2])
                            db.update_lesson_video_info(
                                course_id=course_id,
                                module_number=module_number,
                                lesson_index=lesson_index,
                                video_id=video_id,
                                video_download_url=status.get("download_url"),
                                video_status="completed",
                                video_generated_at=datetime.now(),
                            )
                            logger.info(
                                f"Информация о видео {video_id} сохранена в БД"
                            )
                        except (ValueError, TypeError) as e:
                            logger.warning(
                                f"Не удалось сохранить информацию о видео в БД: {e}"
                            )
        return {"success": True, "data": status}
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса видео {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/lesson/{course_id}/{module_number}/{lesson_index}/info")
async def get_lesson_video_info(course_id: int, module_number: int, lesson_index: int):
    try:
        logger.info(
            f"Запрос информации о видео для урока: {course_id}/{module_number}/{lesson_index}"
        )
        lesson_content = db.get_lesson_content(course_id, module_number, lesson_index)
        logger.debug(f"Контент урока получен из БД: {lesson_content is not None}")
        if lesson_content and lesson_content.get("video_info"):
            video_info = lesson_content["video_info"]
            video_id = video_info.get("video_id")
            video_status = video_info.get("video_status")
            download_url = video_info.get("video_download_url")
            if video_status == "completed" and video_id and not download_url:
                download_url = f"https://resource2.heygen.ai/video/transcode/{video_id}/1280x720.mp4"
                logger.info(
                    f"✅ Сгенерирован URL для скачивания видео {video_id} из БД: {download_url}"
                )
                db.update_lesson_video_info(
                    course_id=course_id,
                    module_number=module_number,
                    lesson_index=lesson_index,
                    video_download_url=download_url,
                )
                video_info["video_download_url"] = download_url
            logger.info(
                f"Найдена информация о видео в БД: video_id={video_id}, status={video_status}, has_url={bool(download_url)}"
            )
            return {"success": True, "data": video_info}

        logger.info("Видео не найдено в БД, проверяем кэш...")
        lesson_key = f"{course_id}_{module_number}_{lesson_index}"
        try:
            cached_video = (
                video_cache_service.cache.get(lesson_key)
                if hasattr(video_cache_service, "cache")
                else None
            )
            if cached_video:
                cached_video_id = cached_video.video_id
                cached_status = cached_video.status
                cached_download_url = cached_video.download_url
                if cached_status == "completed" and cached_video_id and not cached_download_url:
                    cached_download_url = f"https://resource2.heygen.ai/video/transcode/{cached_video_id}/1280x720.mp4"
                    logger.info(
                        f"✅ Сгенерирован URL для скачивания видео {cached_video_id} из кэша: {cached_download_url}"
                    )
                    cached_video.download_url = cached_download_url
                    video_cache_service._save_cache()
                logger.info(
                    f"Найдена информация о видео в кэше: video_id={cached_video_id}, status={cached_status}, has_url={bool(cached_download_url)}"
                )
                video_info = {
                    "video_id": cached_video_id,
                    "video_status": cached_status,
                    "video_download_url": cached_download_url,
                    "video_generated_at": cached_video.created_at.isoformat()
                    if cached_video.created_at
                    else None,
                }
                db.update_lesson_video_info(
                    course_id=course_id,
                    module_number=module_number,
                    lesson_index=lesson_index,
                    video_id=cached_video_id,
                    video_download_url=cached_download_url,
                    video_status=cached_status,
                    video_generated_at=cached_video.created_at
                    if cached_video.created_at
                    else None,
                )
                return {"success": True, "data": video_info}
        except Exception as cache_error:
            logger.warning(f"Ошибка проверки кэша: {cache_error}")

        logger.info(
            f"Видео для урока {course_id}/{module_number}/{lesson_index} не найдено ни в БД, ни в кэше"
        )
        return {"success": True, "data": None, "message": "Видео для этого урока не найдено"}
    except Exception as e:
        logger.error(
            f"Ошибка при получении информации о видео: {str(e)}", exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    try:
        avatars = await video_service.get_available_avatars()
        return {
            "success": True,
            "status": "healthy",
            "heygen_api": "available",
            "avatars_count": len(avatars),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Ошибка при проверке здоровья сервиса: {str(e)}")
        return {
            "success": False,
            "status": "unhealthy",
            "heygen_api": "unavailable",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@router.post("/batch-status")
async def check_batch_video_status(video_ids: List[str]):
    try:
        results = []
        for video_id in video_ids:
            status = await video_service.check_video_status(video_id)
            results.append(status)
        return {"success": True, "data": results, "total": len(results)}
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса видео: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


