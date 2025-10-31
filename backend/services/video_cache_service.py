"""
Сервис для управления кэшем видео (локальный JSON‑кэш).

Используемые библиотеки и компоненты:
- `json`, `pathlib.Path` — хранение кэша в файле JSON.
- `datetime` — отметки времени создания/обновления.
- `logging` — журналирование операций.
"""
import json
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from ..models.video_cache_models import VideoCache, VideoGenerationRequest, VideoGenerationResponse

logger = logging.getLogger(__name__)

class VideoCacheService:
    """Высокоуровневый API к локальному JSON‑кэшу видео.

    Позволяет сохранять/читать статусы генерации, ссылки на скачивание,
    а также получать статистику кэша.
    """
    
    def __init__(self, cache_file: str = "video_cache.json"):
        self.cache_file = Path(cache_file)
        self.cache: Dict[str, VideoCache] = {}
        self._load_cache()
    
    def _load_cache(self):
        """Загружает кэш из файла"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, video_data in data.items():
                        # Преобразуем строки дат обратно в datetime
                        video_data['created_at'] = datetime.fromisoformat(video_data['created_at'])
                        video_data['updated_at'] = datetime.fromisoformat(video_data['updated_at'])
                        self.cache[key] = VideoCache(**video_data)
                logger.info(f"Загружен кэш видео: {len(self.cache)} записей")
            else:
                logger.info("Файл кэша видео не найден, создаем новый")
        except Exception as e:
            logger.error(f"Ошибка загрузки кэша видео: {e}")
            self.cache = {}
    
    def _save_cache(self):
        """Сохраняет кэш в файл"""
        try:
            # Преобразуем datetime в строки для JSON
            cache_data = {}
            for key, video in self.cache.items():
                video_dict = video.dict()
                video_dict['created_at'] = video.created_at.isoformat()
                video_dict['updated_at'] = video.updated_at.isoformat()
                cache_data[key] = video_dict
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Кэш видео сохранен: {len(self.cache)} записей")
        except Exception as e:
            logger.error(f"Ошибка сохранения кэша видео: {e}")
    
    def _generate_lesson_key(self, course_id: int, module_number: int, lesson_index: int) -> str:
        """Генерирует уникальный ключ для урока"""
        return f"{course_id}_{module_number}_{lesson_index}"
    
    def _generate_content_hash(self, content: str) -> str:
        """Генерирует хэш содержимого для сравнения"""
        import hashlib
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def get_cached_video(self, course_id: int, module_number: int, lesson_index: int, 
                        content: str) -> Optional[VideoCache]:
        """
        Получает кэшированное видео для урока
        
        Args:
            course_id: ID курса
            module_number: Номер модуля
            lesson_index: Индекс урока
            content: Содержимое урока для сравнения
            
        Returns:
            VideoCache если найдено подходящее видео, иначе None
        """
        lesson_key = self._generate_lesson_key(course_id, module_number, lesson_index)
        content_hash = self._generate_content_hash(content)
        
        if lesson_key in self.cache:
            cached_video = self.cache[lesson_key]
            
            # Проверяем, что содержимое не изменилось
            cached_content_hash = self._generate_content_hash(cached_video.content)
            if cached_content_hash == content_hash:
                # Используем кэш если видео завершено или еще генерируется
                if cached_video.status == "completed":
                    logger.info(f"Найдено завершенное кэшированное видео для урока {lesson_key}: {cached_video.video_id}")
                    return cached_video
                elif cached_video.status == "generating" and cached_video.video_id:
                    logger.info(f"Найдено генерирующееся кэшированное видео для урока {lesson_key}: {cached_video.video_id}")
                    return cached_video
                else:
                    logger.info(f"Кэшированное видео для урока {lesson_key} имеет статус {cached_video.status}, пропускаем")
            else:
                logger.info(f"Содержимое урока {lesson_key} изменилось (хэш: {cached_content_hash} != {content_hash})")
        
        return None
    
    def cache_video(self, course_id: int, module_number: int, lesson_index: int,
                   request: VideoGenerationRequest, video_id: str, status: str,
                   download_url: Optional[str] = None, error_message: Optional[str] = None) -> VideoCache:
        """
        Сохраняет информацию о видео в кэш
        
        Args:
            course_id: ID курса
            module_number: Номер модуля
            lesson_index: Индекс урока
            request: Запрос генерации видео
            video_id: ID видео
            status: Статус видео
            download_url: URL для скачивания
            error_message: Сообщение об ошибке
            
        Returns:
            VideoCache объект
        """
        lesson_key = self._generate_lesson_key(course_id, module_number, lesson_index)
        now = datetime.now()
        
        video_cache = VideoCache(
            video_id=video_id,
            lesson_key=lesson_key,
            title=request.title,
            content=request.content,
            avatar_id=request.avatar_id,
            voice_id=request.voice_id,
            language=request.language,
            quality=request.quality,
            status=status,
            download_url=download_url,
            created_at=now,
            updated_at=now,
            error_message=error_message
        )
        
        self.cache[lesson_key] = video_cache
        self._save_cache()
        
        logger.info(f"Видео {video_id} сохранено в кэш для урока {lesson_key}")
        return video_cache
    
    def update_video_status(self, video_id: str, status: str, 
                           download_url: Optional[str] = None,
                           duration: Optional[float] = None,
                           file_size: Optional[int] = None,
                           error_message: Optional[str] = None,
                           error_code: Optional[str] = None):
        """
        Обновляет статус видео в кэше
        
        Args:
            video_id: ID видео
            status: Новый статус
            download_url: URL для скачивания
            duration: Длительность видео
            file_size: Размер файла
            error_message: Сообщение об ошибке
            error_code: Код ошибки
        """
        for lesson_key, video_cache in self.cache.items():
            if video_cache.video_id == video_id:
                video_cache.status = status
                video_cache.updated_at = datetime.now()
                
                if download_url:
                    video_cache.download_url = download_url
                if duration:
                    video_cache.duration = duration
                if file_size:
                    video_cache.file_size = file_size
                if error_message:
                    video_cache.error_message = error_message
                if error_code:
                    video_cache.error_code = error_code
                
                self._save_cache()
                logger.info(f"Статус видео {video_id} обновлен: {status}")
                return
        
        logger.warning(f"Видео {video_id} не найдено в кэше для обновления")
    
    def get_video_by_id(self, video_id: str) -> Optional[VideoCache]:
        """Получает видео по ID"""
        for video_cache in self.cache.values():
            if video_cache.video_id == video_id:
                return video_cache
        return None
    
    def delete_video(self, course_id: int, module_number: int, lesson_index: int) -> bool:
        """
        Удаляет видео из кэша
        
        Args:
            course_id: ID курса
            module_number: Номер модуля
            lesson_index: Индекс урока
            
        Returns:
            True если видео удалено, False если не найдено
        """
        lesson_key = self._generate_lesson_key(course_id, module_number, lesson_index)
        
        if lesson_key in self.cache:
            del self.cache[lesson_key]
            self._save_cache()
            logger.info(f"Видео для урока {lesson_key} удалено из кэша")
            return True
        
        return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Возвращает статистику кэша"""
        total_videos = len(self.cache)
        completed_videos = sum(1 for v in self.cache.values() if v.status == "completed")
        failed_videos = sum(1 for v in self.cache.values() if v.status == "failed")
        generating_videos = sum(1 for v in self.cache.values() if v.status == "generating")
        
        return {
            "total_videos": total_videos,
            "completed_videos": completed_videos,
            "failed_videos": failed_videos,
            "generating_videos": generating_videos,
            "cache_file": str(self.cache_file)
        }
