"""
Роуты генерации видео (создание/перегенерация, пакетная генерация).
"""
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from typing import Dict, Any
import logging

from .video_dependencies import video_service, heygen_service, video_cache_service
from ..models.video_cache_models import VideoGenerationRequest, VideoGenerationResponse
from ..database import db
from datetime import datetime


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/video", tags=["video"])


@router.post("/generate-lesson-cached")
async def generate_lesson_with_video_cached(
    course_id: int,
    module_number: int,
    lesson_index: int,
    request: VideoGenerationRequest,
):
    try:
        logger.info(
            f"Запрос на генерацию видео для урока {course_id}_{module_number}_{lesson_index}"
        )

        if not request.regenerate:
            cached_video = video_cache_service.get_cached_video(
                course_id, module_number, lesson_index, request.content
            )
            if cached_video:
                logger.info(
                    f"Используем кэшированное видео: {cached_video.video_id}, статус: {cached_video.status}"
                )
                if cached_video.status == "generating":
                    message = "Видео найдено в кэше и продолжает генерироваться"
                elif cached_video.status == "completed":
                    message = "Видео найдено в кэше и готово"
                else:
                    message = f"Видео найдено в кэше со статусом: {cached_video.status}"
                return VideoGenerationResponse(
                    success=True,
                    video_id=cached_video.video_id,
                    status=cached_video.status,
                    message=message,
                    is_cached=True,
                    download_url=cached_video.download_url,
                )

        logger.info(
            f"Генерируем {'новое' if not request.regenerate else 'перегенерированное'} видео"
        )
        try:
            video_response = await run_in_threadpool(
                heygen_service.create_video_from_text,
                text=request.content,
                avatar_id=request.avatar_id,
                voice_id=request.voice_id,
                language=request.language,
                quality=request.quality,
            )
            logger.info(f"Ответ от HeyGen API: {video_response}")
            video_id = video_response.get("video_id")
            if not video_id:
                error_msg = video_response.get("error", "Неизвестная ошибка генерации")
                logger.error(f"Ошибка генерации видео: {error_msg}")
                existing_video = (
                    video_cache_service.get_video_by_id(video_id) if video_id else None
                )
                if not existing_video:
                    video_cache_service.cache_video(
                        course_id,
                        module_number,
                        lesson_index,
                        request,
                        "",
                        "failed",
                        error_message=error_msg,
                    )
                return VideoGenerationResponse(
                    success=False,
                    status="failed",
                    message=f"Ошибка генерации видео: {error_msg}",
                    error=error_msg,
                )

            if request.regenerate:
                logger.info("Перегенерация видео - удаляем старое из кэша")
                video_cache_service.delete_video(course_id, module_number, lesson_index)

            video_cache_service.cache_video(
                course_id, module_number, lesson_index, request, video_id, "generating"
            )

            db.update_lesson_video_info(
                course_id=course_id,
                module_number=module_number,
                lesson_index=lesson_index,
                video_id=video_id,
                video_status="generating",
                video_generated_at=datetime.now(),
            )

            logger.info(f"Видео {video_id} поставлено в очередь генерации")
            return VideoGenerationResponse(
                success=True,
                video_id=video_id,
                status="generating",
                message="Видео поставлено в очередь генерации",
                is_cached=False,
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Ошибка при создании видео: {error_msg}", exc_info=True)
            if "limit exceeded" not in error_msg.lower() and "timeout" not in error_msg.lower():
                video_cache_service.cache_video(
                    course_id, module_number, lesson_index, request, "", "failed", error_message=error_msg
                )
            return VideoGenerationResponse(
                success=False,
                status="failed",
                message=f"Ошибка при создании видео: {error_msg}",
                error=error_msg,
            )
    except Exception as e:
        logger.error(
            f"Неожиданная ошибка в generate_lesson_with_video_cached: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-lesson")
async def generate_lesson_with_video(lesson_data: Dict[str, Any]):
    try:
        logger.info(
            f"Запрос на генерацию урока с видео: {lesson_data.get('title')}"
        )
        import asyncio

        try:
            result = await asyncio.wait_for(
                video_service.generate_lesson_with_video(lesson_data), timeout=300
            )
        except asyncio.TimeoutError:
            logger.error("Генерация видео превысила время ожидания (5 минут)")
            raise HTTPException(
                status_code=408,
                detail="Генерация видео превысила время ожидания. Попробуйте еще раз.",
            )
        return {"success": True, "data": result, "message": "Урок с видео успешно сгенерирован"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при генерации урока с видео: {str(e)}")
        error_message = str(e)
        if "HeyGen API limit exceeded" in error_message:
            raise HTTPException(
                status_code=429,
                detail="Превышен лимит HeyGen API (5 видео в день). Попробуйте завтра.",
            )
        elif "HeyGen generation failed" in error_message:
            raise HTTPException(status_code=400, detail=f"Ошибка генерации HeyGen: {error_message}")
        elif "HeyGen API HTTP error" in error_message:
            raise HTTPException(status_code=502, detail=f"Ошибка HeyGen API: {error_message}")
        else:
            raise HTTPException(status_code=500, detail=f"Ошибка генерации видео: {error_message}")


@router.post("/generate-lesson-slides")
async def generate_lesson_with_slide_videos(lesson_data: Dict[str, Any]):
    try:
        logger.info(
            f"Запрос на генерацию урока с видео для слайдов: {lesson_data.get('title')}"
        )
        result = await video_service.generate_lesson_with_slide_videos(lesson_data)
        return {
            "success": True,
            "data": result,
            "message": f"Урок с видео для {result.get('total_slides', 0)} слайдов успешно сгенерирован",
        }
    except Exception as e:
        logger.error(
            f"Ошибка при генерации урока с видео для слайдов: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-course")
async def generate_course_with_videos(course_data: Dict[str, Any]):
    try:
        logger.info(
            f"Запрос на генерацию курса с видео: {course_data.get('title')}"
        )
        result = await video_service.generate_course_videos(course_data)
        return {
            "success": True,
            "data": result,
            "message": f"Видео для курса '{course_data.get('title')}' поставлены в очередь генерации",
        }
    except Exception as e:
        logger.error(f"Ошибка при генерации курса с видео: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retry/{video_id}")
async def retry_video_generation(video_id: str, lesson_data: Dict[str, Any]):
    try:
        logger.info(
            f"Повторная генерация видео для урока: {lesson_data.get('title')}"
        )
        result = await video_service.generate_lesson_with_video(lesson_data)
        return {
            "success": True,
            "data": result,
            "message": f"Видео для урока '{lesson_data.get('title')}' пересоздано",
        }
    except Exception as e:
        logger.error(f"Ошибка при повторной генерации видео: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


