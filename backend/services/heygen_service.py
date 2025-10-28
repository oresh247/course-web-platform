"""
HeyGen API Service для генерации видео-контента
Интеграция с HeyGen для создания AI аватаров и видео по урокам
"""

import os
import requests
import json
import time
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import logging
import ssl

load_dotenv()

# Настройка SSL для корпоративных сетей
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

# Отключаем проверку SSL сертификатов
ssl._create_default_https_context = ssl._create_unverified_context

logger = logging.getLogger(__name__)

class HeyGenService:
    """Сервис для работы с HeyGen API"""
    
    def __init__(self):
        self.api_key = os.getenv('HEYGEN_API_KEY')
        self.base_url = os.getenv('HEYGEN_API_URL', 'https://api.heygen.com')
        
        if not self.api_key:
            raise ValueError("HEYGEN_API_KEY не найден в переменных окружения")
        
        self.headers = {
            'X-Api-Key': self.api_key,  # Правильный заголовок
            'Content-Type': 'application/json'
        }
        
        logger.info("HeyGen сервис инициализирован")
    
    def create_video_from_text(self, 
                             text: str, 
                             avatar_id: str = "default",
                             voice_id: str = "default",
                             background_id: Optional[str] = None,
                             language: str = "ru",
                             quality: str = "high",
                             test_mode: bool = False) -> Dict[str, Any]:
        """
        Создает видео из текста с использованием AI аватара
        
        Args:
            text: Текст для озвучивания
            avatar_id: ID аватара HeyGen
            voice_id: ID голоса
            background_id: ID фона (опционально)
            language: Язык озвучивания
            
        Returns:
            Dict с информацией о созданном видео
        """
        payload = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": avatar_id,
                        "avatar_style": "normal"
                    },
                    "voice": {
                        "type": "text",
                        "input_text": text,
                        "voice_id": voice_id,
                        "language": language
                    },
                    "background": {
                        "type": "color",
                        "value": "#ffffff"
                    } if not background_id else {
                        "type": "image",
                        "value": background_id
                    }
                }
            ],
            "dimension": {
                "width": 1920 if quality == "high" else 1280,
                "height": 1080 if quality == "high" else 720
            },
            "aspect_ratio": "16:9",
            "quality": quality,
            "test": test_mode
        }
        
        try:
            logger.info(f"Создание видео с аватаром {avatar_id} и голосом {voice_id}")
            response = requests.post(
                f"{self.base_url}/v2/video/generate",
                headers=self.headers,
                json=payload,
                timeout=30,
                verify=False
            )
            response.raise_for_status()
            result = response.json()
            logger.info(f"Видео создано успешно: {result.get('video_id')}")
            return result
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка HeyGen API при создании видео: {str(e)}")
            raise Exception(f"HeyGen API error: {str(e)}")
    
    def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """
        Проверяет статус генерации видео
        
        Args:
            video_id: ID видео для проверки
            
        Returns:
            Dict с информацией о статусе видео
        """
        try:
            response = requests.get(
                f"{self.base_url}/v1/video_status.get?video_id={video_id}",
                headers=self.headers,
                timeout=10,
                verify=False
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при проверке статуса видео {video_id}: {str(e)}")
            raise Exception(f"HeyGen API error: {str(e)}")
    
    def download_video(self, video_id: str, output_path: str) -> bool:
        """
        Скачивает готовое видео
        
        Args:
            video_id: ID видео для скачивания
            output_path: Путь для сохранения файла
            
        Returns:
            True если скачивание успешно
        """
        try:
            logger.info(f"Скачивание видео {video_id} в {output_path}")
            response = requests.get(
                f"{self.base_url}/v1/video/{video_id}/download",
                headers=self.headers,
                stream=True,
                timeout=60,
                verify=False
            )
            response.raise_for_status()
            
            # Создаем директорию если не существует
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Видео {video_id} успешно скачано")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при скачивании видео {video_id}: {str(e)}")
            raise Exception(f"HeyGen API error: {str(e)}")
    
    def get_available_avatars(self) -> Dict[str, Any]:
        """
        Получает список доступных аватаров
        
        Returns:
            Dict с информацией об аватарах
        """
        try:
            logger.info("Запрос списка аватаров HeyGen...")
            response = requests.get(
                f"{self.base_url}/v2/avatars",
                headers=self.headers,
                timeout=10,
                verify=False
            )
            
            logger.info(f"Ответ HeyGen API: статус {response.status_code}")
            
            if response.status_code == 403:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get('message', 'Access forbidden')
                error_code = error_data.get('code', 'N/A')
                logger.error(f"HeyGen API 403: {error_msg} (код: {error_code})")
                raise Exception(f"HeyGen API access forbidden: {error_msg}")
            
            response.raise_for_status()
            result = response.json()
            logger.info(f"Получено аватаров: {len(result.get('data', []))}")
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при получении списка аватаров: {str(e)}")
            raise Exception(f"HeyGen API error: {str(e)}")
    
    def get_available_voices(self) -> Dict[str, Any]:
        """
        Получает список доступных голосов
        
        Returns:
            Dict с информацией о голосах
        """
        try:
            response = requests.get(
                f"{self.base_url}/v1/voice.list",
                headers=self.headers,
                timeout=10,
                verify=False
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при получении списка голосов: {str(e)}")
            raise Exception(f"HeyGen API error: {str(e)}")
    
    def wait_for_video_completion(self, video_id: str, max_wait_time: int = 300) -> Dict[str, Any]:
        """
        Ожидает завершения генерации видео
        
        Args:
            video_id: ID видео
            max_wait_time: Максимальное время ожидания в секундах
            
        Returns:
            Dict с финальным статусом видео
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                status = self.get_video_status(video_id)
                video_status = status.get('status', 'unknown')
                
                logger.info(f"Статус видео {video_id}: {video_status}")
                
                if video_status == 'completed':
                    return status
                elif video_status == 'failed':
                    raise Exception(f"Генерация видео {video_id} завершилась с ошибкой")
                
                time.sleep(10)  # Ждем 10 секунд перед следующей проверкой
                
            except Exception as e:
                logger.error(f"Ошибка при ожидании завершения видео {video_id}: {str(e)}")
                raise
        
        raise Exception(f"Превышено время ожидания для видео {video_id}")
    
    def create_lesson_video(self, 
                          lesson_title: str,
                          lesson_content: str,
                          avatar_id: str = "default",
                          voice_id: str = "default") -> Dict[str, Any]:
        """
        Создает видео для урока с оптимизированным скриптом
        
        Args:
            lesson_title: Название урока
            lesson_content: Содержание урока
            avatar_id: ID аватара
            voice_id: ID голоса
            
        Returns:
            Dict с информацией о созданном видео
        """
        # Подготавливаем скрипт для видео
        video_script = self._prepare_lesson_script(lesson_title, lesson_content)
        
        # Создаем видео
        video_response = self.create_video_from_text(
            text=video_script,
            avatar_id=avatar_id,
            voice_id=voice_id,
            language="ru"
        )
        
        return {
            'video_id': video_response.get('video_id'),
            'script': video_script,
            'status': 'generating',
            'created_at': time.time()
        }
    
    def _prepare_lesson_script(self, title: str, content: str) -> str:
        """
        Подготавливает скрипт для видео урока
        
        Args:
            title: Название урока
            content: Содержание урока
            
        Returns:
            Оптимизированный скрипт для видео
        """
        # Ограничиваем длину скрипта для HeyGen (рекомендуется до 2000 символов)
        max_length = 2000
        
        script_parts = []
        
        # Приветствие
        script_parts.append(f"Привет! Добро пожаловать на урок: {title}")
        
        # Основное содержание (сокращаем если нужно)
        if len(content) > max_length - len(script_parts[0]) - 50:
            # Берем первые символы и добавляем многоточие
            truncated_content = content[:max_length - len(script_parts[0]) - 50] + "..."
            script_parts.append(truncated_content)
        else:
            script_parts.append(content)
        
        # Заключение
        script_parts.append("Спасибо за внимание! До встречи на следующем уроке!")
        
        final_script = " ".join(script_parts)
        
        # Дополнительная проверка длины
        if len(final_script) > max_length:
            final_script = final_script[:max_length-3] + "..."
        
        return final_script
    
    def get_video_download_url(self, video_id: str) -> Optional[str]:
        """
        Получает URL для скачивания видео
        
        Args:
            video_id: ID видео
            
        Returns:
            URL для скачивания или None
        """
        try:
            status = self.get_video_status(video_id)
            if status.get('status') == 'completed':
                return status.get('download_url')
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении URL скачивания для {video_id}: {str(e)}")
            return None
