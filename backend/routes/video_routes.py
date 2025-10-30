"""
API роуты для работы с HeyGen видео-генерацией
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from ..services.video_generation_service import VideoGenerationService
from ..services.heygen_service import HeyGenService
from ..services.video_cache_service import VideoCacheService
from ..models.video_cache_models import VideoGenerationRequest, VideoGenerationResponse
from ..database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/video", tags=["video"])

# Инициализация сервисов
video_service = VideoGenerationService()
heygen_service = HeyGenService()
video_cache_service = VideoCacheService()

@router.post("/generate-lesson-cached")
async def generate_lesson_with_video_cached(
    course_id: int,
    module_number: int, 
    lesson_index: int,
    request: VideoGenerationRequest
):
    """
    Генерирует видео для урока с кэшированием
    
    Args:
        course_id: ID курса
        module_number: Номер модуля
        lesson_index: Индекс урока
        request: Данные для генерации видео
        
    Returns:
        VideoGenerationResponse с информацией о видео
    """
    try:
        logger.info(f"Запрос на генерацию видео для урока {course_id}_{module_number}_{lesson_index}")
        
        # Проверяем кэш, если не принудительная перегенерация
        if not request.regenerate:
            cached_video = video_cache_service.get_cached_video(
                course_id, module_number, lesson_index, request.content
            )
            
            if cached_video:
                logger.info(f"Используем кэшированное видео: {cached_video.video_id}, статус: {cached_video.status}")
                
                # Если видео еще генерируется, возвращаем его для продолжения отслеживания
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
                    download_url=cached_video.download_url
                )
        
        # Генерируем новое видео или перегенерируем существующее
        logger.info(f"Генерируем {'новое' if not request.regenerate else 'перегенерированное'} видео")
        
        try:
            video_response = heygen_service.create_video_from_text(
                text=request.content,
                avatar_id=request.avatar_id,
                voice_id=request.voice_id,
                language=request.language,
                quality=request.quality
            )
            
            # Логируем полный ответ для диагностики
            logger.info(f"Ответ от HeyGen API: {video_response}")
            
            video_id = video_response.get('video_id')
            if not video_id:
                error_msg = video_response.get('error', 'Неизвестная ошибка генерации')
                logger.error(f"Ошибка генерации видео: {error_msg}")
                
                # Если есть существующее видео в кэше при перегенерации, обновляем его статус
                lesson_key = f"{course_id}_{module_number}_{lesson_index}"
                existing_video = video_cache_service.get_video_by_id(video_id) if video_id else None
                
                if not existing_video:
                    # Сохраняем ошибку в кэш
                    video_cache_service.cache_video(
                        course_id, module_number, lesson_index,
                        request, "", "failed", error_message=error_msg
                    )
                
                return VideoGenerationResponse(
                    success=False,
                    status="failed",
                    message=f"Ошибка генерации видео: {error_msg}",
                    error=error_msg
                )
            
            # При перегенерации удаляем старое видео из кэша, если оно есть
            if request.regenerate:
                logger.info("Перегенерация видео - удаляем старое из кэша")
                video_cache_service.delete_video(course_id, module_number, lesson_index)
            
            # Сохраняем новое видео в кэш
            video_cache_service.cache_video(
                course_id, module_number, lesson_index,
                request, video_id, "generating"
            )
            
            # Сохраняем начальную информацию о видео в базу данных
            db.update_lesson_video_info(
                course_id=course_id,
                module_number=module_number,
                lesson_index=lesson_index,
                video_id=video_id,
                video_status='generating',
                video_generated_at=datetime.now()
            )
            
            logger.info(f"Видео {video_id} поставлено в очередь генерации")
            
            return VideoGenerationResponse(
                success=True,
                video_id=video_id,
                status="generating",
                message="Видео поставлено в очередь генерации",
                is_cached=False
            )
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Ошибка при создании видео: {error_msg}", exc_info=True)
            
            # Сохраняем ошибку в кэш только если это не таймаут или сетевая ошибка
            # (в этих случаях видео может создаваться, но мы получили ошибку до ответа)
            if "limit exceeded" not in error_msg.lower() and "timeout" not in error_msg.lower():
                video_cache_service.cache_video(
                    course_id, module_number, lesson_index,
                    request, "", "failed", error_message=error_msg
                )
            
            return VideoGenerationResponse(
                success=False,
                status="failed",
                message=f"Ошибка при создании видео: {error_msg}",
                error=error_msg
            )
            
    except Exception as e:
        logger.error(f"Неожиданная ошибка в generate_lesson_with_video_cached: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
        
        # Добавляем таймаут для всего процесса генерации
        import asyncio
        try:
            result = await asyncio.wait_for(
                video_service.generate_lesson_with_video(lesson_data),
                timeout=300  # 5 минут таймаут
            )
        except asyncio.TimeoutError:
            logger.error("Генерация видео превысила время ожидания (5 минут)")
            raise HTTPException(
                status_code=408, 
                detail="Генерация видео превысила время ожидания. Попробуйте еще раз."
            )
        
        return {
            "success": True,
            "data": result,
            "message": "Урок с видео успешно сгенерирован"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при генерации урока с видео: {str(e)}")
        
        # Определяем тип ошибки и возвращаем соответствующий статус
        error_message = str(e)
        if "HeyGen API limit exceeded" in error_message:
            raise HTTPException(
                status_code=429, 
                detail="Превышен лимит HeyGen API (5 видео в день). Попробуйте завтра."
            )
        elif "HeyGen generation failed" in error_message:
            raise HTTPException(
                status_code=400, 
                detail=f"Ошибка генерации HeyGen: {error_message}"
            )
        elif "HeyGen API HTTP error" in error_message:
            raise HTTPException(
                status_code=502, 
                detail=f"Ошибка HeyGen API: {error_message}"
            )
        else:
            raise HTTPException(status_code=500, detail=f"Ошибка генерации видео: {error_message}")

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
    Проверяет статус генерации видео и обновляет кэш
    
    Args:
        video_id: ID видео для проверки
        
    Returns:
        Dict с информацией о статусе видео
    """
    try:
        status = await video_service.check_video_status(video_id)
        
        # Обновляем кэш с новым статусом
        if status:
            video_status = status.get('status', 'unknown')
            download_url = status.get('download_url')
            
            # Если статус completed, но нет download_url, генерируем URL для скачивания
            # URL для скачивания: https://resource2.heygen.ai/video/transcode/{video_id}/1280x720.mp4
            if video_status == 'completed' and not download_url:
                download_url = f"https://resource2.heygen.ai/video/transcode/{video_id}/1280x720.mp4"
                logger.info(f"✅ Сгенерирован URL для скачивания видео {video_id}: {download_url}")
                status['download_url'] = download_url
            
            video_cache_service.update_video_status(
                video_id=video_id,
                status=video_status,
                download_url=download_url,
                duration=status.get('duration'),
                file_size=status.get('file_size'),
                error_message=status.get('error'),
                error_code=status.get('error_code')
            )
            
            # Если видео завершено, сохраняем информацию в базу данных
            if video_status == 'completed' and download_url:
                # Находим урок по video_id из кэша
                cached_video = video_cache_service.get_video_by_id(video_id)
                if cached_video:
                    # Парсим lesson_key для получения course_id, module_number, lesson_index
                    parts = cached_video.lesson_key.split('_')
                    if len(parts) == 3:
                        try:
                            course_id = int(parts[0])
                            module_number = int(parts[1])
                            lesson_index = int(parts[2])
                            
                            # Сохраняем в базу данных
                            db.update_lesson_video_info(
                                course_id=course_id,
                                module_number=module_number,
                                lesson_index=lesson_index,
                                video_id=video_id,
                                video_download_url=status.get('download_url'),
                                video_status='completed',
                                video_generated_at=datetime.now()
                            )
                            logger.info(f"Информация о видео {video_id} сохранена в БД")
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Не удалось сохранить информацию о видео в БД: {e}")
        
        return {
            "success": True,
            "data": status
        }
        
    except Exception as e:
        logger.error(f"Ошибка при проверке статуса видео {video_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lesson/{course_id}/{module_number}/{lesson_index}/info")
async def get_lesson_video_info(course_id: int, module_number: int, lesson_index: int):
    """
    Получает информацию о видео для урока
    Проверяет и БД, и кэш видео
    
    Args:
        course_id: ID курса
        module_number: Номер модуля
        lesson_index: Индекс урока
        
    Returns:
        Dict с информацией о видео
    """
    try:
        logger.info(f"Запрос информации о видео для урока: {course_id}/{module_number}/{lesson_index}")
        
        # Сначала проверяем БД
        lesson_content = db.get_lesson_content(course_id, module_number, lesson_index)
        logger.debug(f"Контент урока получен из БД: {lesson_content is not None}")
        
        if lesson_content and lesson_content.get('video_info'):
            video_info = lesson_content['video_info']
            video_id = video_info.get('video_id')
            video_status = video_info.get('video_status')
            download_url = video_info.get('video_download_url')
            
            # Если статус completed, но нет download_url, генерируем URL для скачивания
            if video_status == 'completed' and video_id and not download_url:
                download_url = f"https://resource2.heygen.ai/video/transcode/{video_id}/1280x720.mp4"
                logger.info(f"✅ Сгенерирован URL для скачивания видео {video_id} из БД: {download_url}")
                # Обновляем URL в БД
                db.update_lesson_video_info(
                    course_id=course_id,
                    module_number=module_number,
                    lesson_index=lesson_index,
                    video_download_url=download_url
                )
                video_info['video_download_url'] = download_url
            
            logger.info(f"Найдена информация о видео в БД: video_id={video_id}, status={video_status}, has_url={bool(download_url)}")
            
            return {
                "success": True,
                "data": video_info
            }
        
        # Если в БД нет, проверяем кэш видео
        logger.info(f"Видео не найдено в БД, проверяем кэш...")
        lesson_key = f"{course_id}_{module_number}_{lesson_index}"
        
        # Получаем из кэша (нужно получить контент урока для проверки хэша)
        # Но для этого нужен контент, поэтому просто ищем по lesson_key
        try:
            from ..services.video_cache_service import VideoCacheService
            cache_service = VideoCacheService()
            
            # Пытаемся найти видео в кэше по lesson_key
            cached_video = cache_service.cache.get(lesson_key) if hasattr(cache_service, 'cache') else None
            
            if cached_video:
                cached_video_id = cached_video.video_id
                cached_status = cached_video.status
                cached_download_url = cached_video.download_url
                
                # Если статус completed, но нет download_url, генерируем URL для скачивания
                if cached_status == 'completed' and cached_video_id and not cached_download_url:
                    cached_download_url = f"https://resource2.heygen.ai/video/transcode/{cached_video_id}/1280x720.mp4"
                    logger.info(f"✅ Сгенерирован URL для скачивания видео {cached_video_id} из кэша: {cached_download_url}")
                    # Обновляем URL в кэше
                    cached_video.download_url = cached_download_url
                    cache_service._save_cache()
                
                logger.info(f"Найдена информация о видео в кэше: video_id={cached_video_id}, status={cached_status}, has_url={bool(cached_download_url)}")
                
                video_info = {
                    'video_id': cached_video_id,
                    'video_status': cached_status,
                    'video_download_url': cached_download_url,
                    'video_generated_at': cached_video.created_at.isoformat() if cached_video.created_at else None
                }
                
                # Сохраняем в БД для постоянного хранения
                db.update_lesson_video_info(
                    course_id=course_id,
                    module_number=module_number,
                    lesson_index=lesson_index,
                    video_id=cached_video_id,
                    video_download_url=cached_download_url,
                    video_status=cached_status,
                    video_generated_at=cached_video.created_at if cached_video.created_at else None
                )
                
                return {
                    "success": True,
                    "data": video_info
                }
        except Exception as cache_error:
            logger.warning(f"Ошибка проверки кэша: {cache_error}")
        
        logger.info(f"Видео для урока {course_id}/{module_number}/{lesson_index} не найдено ни в БД, ни в кэше")
        return {
            "success": True,
            "data": None,
            "message": "Видео для этого урока не найдено"
        }
    except Exception as e:
        logger.error(f"Ошибка при получении информации о видео: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/stats")
async def get_video_cache_stats():
    """
    Возвращает статистику кэша видео
    
    Returns:
        Dict со статистикой кэша
    """
    try:
        stats = video_cache_service.get_cache_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Ошибка при получении статистики кэша: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cache/lesson/{course_id}/{module_number}/{lesson_index}")
async def delete_cached_video(course_id: int, module_number: int, lesson_index: int):
    """
    Удаляет кэшированное видео для урока
    
    Args:
        course_id: ID курса
        module_number: Номер модуля
        lesson_index: Индекс урока
        
    Returns:
        Dict с результатом операции
    """
    try:
        success = video_cache_service.delete_video(course_id, module_number, lesson_index)
        
        if success:
            return {
                "success": True,
                "message": "Кэшированное видео удалено"
            }
        else:
            return {
                "success": False,
                "message": "Кэшированное видео не найдено"
            }
    except Exception as e:
        logger.error(f"Ошибка при удалении кэшированного видео: {str(e)}")
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
