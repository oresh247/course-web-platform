"""
Альтернативная версия HeyGen сервиса для работы без API
"""

import os
import logging
from typing import Dict, Any, Optional, List
from .heygen.interfaces import HeygenClient  # тип-порт для совместимости
from datetime import datetime

logger = logging.getLogger(__name__)

class MockHeyGenService:
    """Мок-сервис HeyGen для работы без API"""
    
    def __init__(self):
        self.api_key = os.getenv('HEYGEN_API_KEY')
        self.base_url = 'https://api.heygen.com/v1'
        
        if not self.api_key:
            logger.warning("HEYGEN_API_KEY не найден - используется мок-режим")
        
        logger.info("MockHeyGen сервис инициализирован")
    
    def create_video_from_text(self, 
                             text: str, 
                             avatar_id: str = "default",
                             voice_id: str = "default",
                             background_id: Optional[str] = None,
                             language: str = "ru") -> Dict[str, Any]:
        """
        Создает мок-видео из текста
        """
        logger.info(f"Мок-создание видео с аватаром {avatar_id} и голосом {voice_id}")
        
        # Генерируем мок ID видео
        video_id = f"mock_video_{int(datetime.now().timestamp())}"
        
        return {
            "video_id": video_id,
            "status": "completed",
            "message": "Мок-видео создано (HeyGen API недоступен)",
            "mock": True
        }
    
    def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """
        Возвращает мок-статус видео
        """
        return {
            "video_id": video_id,
            "status": "completed",
            "progress": 100,
            "download_url": f"https://mock-download.com/{video_id}.mp4",
            "mock": True
        }
    
    def download_video(self, video_id: str, output_path: str) -> bool:
        """
        Мок-скачивание видео
        """
        logger.info(f"Мок-скачивание видео {video_id} в {output_path}")
        
        # Создаем директорию если не существует
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Создаем мок-файл
        with open(output_path, 'w') as f:
            f.write(f"# Мок-видео {video_id}\n")
            f.write(f"# Создано: {datetime.now()}\n")
            f.write(f"# HeyGen API недоступен\n")
        
        logger.info(f"Мок-файл создан: {output_path}")
        return True
    
    def get_available_avatars(self) -> Dict[str, Any]:
        """
        Возвращает мок-список аватаров
        """
        mock_avatars = [
            {
                "avatar_id": "mock_avatar_1",
                "name": "Мок Аватар 1",
                "description": "Тестовый аватар (HeyGen недоступен)",
                "gender": "neutral",
                "age_range": "adult"
            },
            {
                "avatar_id": "mock_avatar_2", 
                "name": "Мок Аватар 2",
                "description": "Тестовый аватар (HeyGen недоступен)",
                "gender": "neutral",
                "age_range": "adult"
            }
        ]
        
        return {
            "data": mock_avatars,
            "total": len(mock_avatars),
            "mock": True
        }
    
    def get_available_voices(self) -> Dict[str, Any]:
        """
        Возвращает мок-список голосов
        """
        mock_voices = [
            {
                "voice_id": "mock_voice_1",
                "name": "Мок Голос 1",
                "language": "ru",
                "gender": "neutral",
                "age_range": "adult"
            },
            {
                "voice_id": "mock_voice_2",
                "name": "Мок Голос 2", 
                "language": "ru",
                "gender": "neutral",
                "age_range": "adult"
            }
        ]
        
        return {
            "data": mock_voices,
            "total": len(mock_voices),
            "mock": True
        }
    
    def wait_for_video_completion(self, video_id: str, max_wait_time: int = 300) -> Dict[str, Any]:
        """
        Мок-ожидание завершения видео
        """
        logger.info(f"Мок-ожидание завершения видео {video_id}")
        
        return {
            "video_id": video_id,
            "status": "completed",
            "download_url": f"https://mock-download.com/{video_id}.mp4",
            "duration": 30,
            "file_size": 1024000,
            "mock": True
        }
    
    def create_lesson_video(self, 
                          lesson_title: str,
                          lesson_content: str,
                          avatar_id: str = "default",
                          voice_id: str = "default") -> Dict[str, Any]:
        """
        Создает мок-видео для урока
        """
        logger.info(f"Мок-создание видео для урока: {lesson_title}")
        
        video_response = self.create_video_from_text(
            text=lesson_content,
            avatar_id=avatar_id,
            voice_id=voice_id,
            language="ru"
        )
        
        return {
            'video_id': video_response['video_id'],
            'script': f"Мок-скрипт для урока '{lesson_title}': {lesson_content[:100]}...",
            'status': 'completed',
            'created_at': datetime.now().timestamp(),
            'mock': True
        }
    
    def get_video_download_url(self, video_id: str) -> Optional[str]:
        """
        Возвращает мок URL для скачивания
        """
        return f"https://mock-download.com/{video_id}.mp4"

class AdaptiveHeyGenService:
    """Адаптивный сервис, который переключается между реальным и мок API"""
    
    def __init__(self):
        self.real_service = None
        self.mock_service = MockHeyGenService()
        self.use_mock = True
        
        # Пытаемся инициализировать реальный сервис
        try:
            from .heygen_service import HeyGenService
            self.real_service = HeyGenService()
            
            # Тестируем подключение
            test_response = self.real_service.get_available_avatars()
            if not test_response.get('mock', False):
                self.use_mock = False
                logger.info("Реальный HeyGen сервис инициализирован")
            else:
                logger.info("Используется мок HeyGen сервис")
                
        except Exception as e:
            logger.warning(f"Не удалось инициализировать реальный HeyGen сервис: {e}")
            logger.info("Используется мок HeyGen сервис")
    
    def get_service(self):
        """Возвращает активный сервис"""
        return self.mock_service if self.use_mock else self.real_service
    
    def create_video_from_text(self, *args, **kwargs):
        return self.get_service().create_video_from_text(*args, **kwargs)
    
    def get_video_status(self, *args, **kwargs):
        return self.get_service().get_video_status(*args, **kwargs)
    
    def download_video(self, *args, **kwargs):
        return self.get_service().download_video(*args, **kwargs)
    
    def get_available_avatars(self, *args, **kwargs):
        return self.get_service().get_available_avatars(*args, **kwargs)
    
    def get_available_voices(self, *args, **kwargs):
        return self.get_service().get_available_voices(*args, **kwargs)
    
    def wait_for_video_completion(self, *args, **kwargs):
        return self.get_service().wait_for_video_completion(*args, **kwargs)
    
    def create_lesson_video(self, *args, **kwargs):
        return self.get_service().create_lesson_video(*args, **kwargs)
    
    def get_video_download_url(self, *args, **kwargs):
        return self.get_service().get_video_download_url(*args, **kwargs)
