"""
API роуты для работы с HeyGen видео-генерацией
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from ..services.video_generation_service import VideoGenerationService
from ..services.heygen_service import HeyGenService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/video", tags=["video"])

# Инициализация сервисов
video_service = VideoGenerationService()
heygen_service = HeyGenService()

@router.post("/generate-lesson")
async def generate_lesson_with_video(lesson_data: Dict[str, Any]):
    """
    Генерирует урок с видео-контентом
    
    Args:
        lesson_data: Данные для генерации урока
        
    Returns:
        Dict с информацией о созданном уроке и видео
    """
    try:
        logger.info(f"Запрос на генерацию урока с видео: {lesson_data.get('title')}")
        
        result = await video_service.generate_lesson_with_video(lesson_data)
        
        return {
            "success": True,
            "data": result,
            "message": "Урок с видео успешно сгенерирован"
        }
        
    except Exception as e:
        logger.error(f"Ошибка при генерации урока с видео: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-lesson-slides")
async def generate_lesson_with_slide_videos(lesson_data: Dict[str, Any]):
    """
    Генерирует урок с видео для каждого слайда
    
    Args:
        lesson_data: Данные для генерации урока
        
    Returns:
        Dict с информацией о созданном уроке и видео для каждого слайда
    """
    try:
        logger.info(f"Запрос на генерацию урока с видео для слайдов: {lesson_data.get('title')}")
        
        result = await video_service.generate_lesson_with_slide_videos(lesson_data)
        
        return {
            "success": True,
            "data": result,
            "message": f"Урок с видео для {result.get('total_slides', 0)} слайдов успешно сгенерирован"
        }
        
    except Exception as e:
        logger.error(f"Ошибка при генерации урока с видео для слайдов: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-course")
async def generate_course_with_videos(course_data: Dict[str, Any]):
    """
    Генерирует весь курс с видео для каждого урока
    
    Args:
        course_data: Данные курса с уроками
        
    Returns:
        Dict с информацией о созданных видео
    """
    try:
        logger.info(f"Запрос на генерацию курса с видео: {course_data.get('title')}")
        
        result = await video_service.generate_course_videos(course_data)
        
        return {
            "success": True,
            "data": result,
            "message": f"Видео для курса '{course_data.get('title')}' поставлены в очередь генерации"
        }
        
    except Exception as e:
        logger.error(f"Ошибка при генерации курса с видео: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{video_id}")
async def get_video_status(video_id: str):
    """
    Проверяет статус генерации видео
    
    Args:
        video_id: ID видео для проверки
        
    Returns:
        Dict с информацией о статусе видео
    """
    try:
        status = await video_service.check_video_status(video_id)
        
        return {
            "success": True,
            "data": status
        }
        
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса видео {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/wait-completion/{video_id}")
async def wait_for_video_completion(video_id: str, max_wait_time: int = 300):
    """
    Ожидает завершения генерации видео
    
    Args:
        video_id: ID видео
        max_wait_time: Максимальное время ожидания в секундах
        
    Returns:
        Dict с финальным статусом видео
    """
    try:
        result = await video_service.wait_for_video_completion(video_id, max_wait_time)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Ошибка при ожидании завершения видео {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download/{video_id}")
async def download_video(video_id: str, output_path: str):
    """
    Скачивает готовое видео
    
    Args:
        video_id: ID видео
        output_path: Путь для сохранения файла
        
    Returns:
        Dict с результатом скачивания
    """
    try:
        success = await video_service.download_video(video_id, output_path)
        
        if success:
            return {
                "success": True,
                "message": f"Видео {video_id} успешно скачано в {output_path}"
            }
        else:
            raise HTTPException(status_code=500, detail="Ошибка при скачивании видео")
            
    except Exception as e:
        logger.error(f"Ошибка при скачивании видео {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/avatars")
async def get_available_avatars():
    """
    Получает список доступных аватаров HeyGen
    
    Returns:
        List с информацией об аватарах
    """
    try:
        avatars = await video_service.get_available_avatars()
        
        return {
            "success": True,
            "data": avatars,
            "count": len(avatars)
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении аватаров: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/voices")
async def get_available_voices():
    """
    Получает список доступных голосов HeyGen
    
    Returns:
        List с информацией о голосах
    """
    try:
        voices = await video_service.get_available_voices()
        
        return {
            "success": True,
            "data": voices,
            "count": len(voices)
        }
        
    except Exception as e:
        logger.error(f"Ошибка при получении голосов: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-status")
async def check_batch_video_status(video_ids: List[str]):
    """
    Проверяет статус нескольких видео одновременно
    
    Args:
        video_ids: Список ID видео для проверки
        
    Returns:
        Dict с статусами всех видео
    """
    try:
        results = []
        
        for video_id in video_ids:
            status = await video_service.check_video_status(video_id)
            results.append(status)
        
        return {
            "success": True,
            "data": results,
            "total": len(results)
        }
        
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса видео: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/retry/{video_id}")
async def retry_video_generation(video_id: str, lesson_data: Dict[str, Any]):
    """
    Повторно генерирует видео для урока
    
    Args:
        video_id: ID неудачного видео
        lesson_data: Данные урока для повторной генерации
        
    Returns:
        Dict с информацией о новом видео
    """
    try:
        logger.info(f"Повторная генерация видео для урока: {lesson_data.get('title')}")
        
        result = await video_service.generate_lesson_with_video(lesson_data)
        
        return {
            "success": True,
            "data": result,
            "message": f"Видео для урока '{lesson_data.get('title')}' пересоздано"
        }
        
    except Exception as e:
        logger.error(f"Ошибка при повторной генерации видео: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    Проверка здоровья сервиса HeyGen
    
    Returns:
        Dict с информацией о состоянии сервиса
    """
    try:
        # Проверяем доступность HeyGen API
        avatars = await video_service.get_available_avatars()
        
        return {
            "success": True,
            "status": "healthy",
            "heygen_api": "available",
            "avatars_count": len(avatars),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка при проверке здоровья сервиса: {str(e)}")
        return {
            "success": False,
            "status": "unhealthy",
            "heygen_api": "unavailable",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
