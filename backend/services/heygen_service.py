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
from backend.clients.heygen_client import HeygenHttpClient
from backend.services.heygen.interfaces import HeygenClient  # порт
from backend.services.heygen.transforms import (
    build_create_video_payload,
    normalize_create_video_response,
)
from backend.services.heygen.normalizers import normalize_status_response

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
        from backend.config import settings
        self.api_key = settings.HEYGEN_API_KEY
        self.base_url = settings.HEYGEN_API_URL
        if not self.api_key:
            raise ValueError("HEYGEN_API_KEY не найден в переменных окружения")
        self.client = HeygenHttpClient(api_key=self.api_key, base_url=self.base_url)
        logger.info("HeyGen сервис инициализирован (через HeygenHttpClient)")
    
    def create_video_from_text(self, 
                             text: str, 
                             avatar_id: str = "Abigail_expressive_2024112501",
                             voice_id: str = "9799f1ba6acd4b2b993fe813a18f9a91",
                             background_id: Optional[str] = None,
                             language: str = "ru",
                             quality: str = "low",
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
        payload = build_create_video_payload(
            text=text,
            avatar_id=avatar_id,
            voice_id=voice_id,
            language=language,
            background_id=background_id,
            quality=quality,
            test_mode=test_mode,
        )
        
        try:
            logger.info(f"Создание видео с аватаром {avatar_id} и голосом {voice_id}")
            from backend.config import settings
            response = self.client.post("/v2/video/generate", json_payload=payload, timeout=settings.HEYGEN_TIMEOUT)
            
            # Логируем статус ответа для диагностики
            logger.info(f"HTTP статус ответа HeyGen: {response.status_code}")
            
            # Проверяем HTTP статус перед парсингом JSON
            if response.status_code == 429:
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', {}).get('message', 'Превышен лимит запросов')
                    error_code = error_data.get('error', {}).get('code', '429')
                except:
                    error_message = 'Превышен лимит запросов к HeyGen API'
                    error_code = '429'
                
                logger.error(f"HeyGen API лимит превышен: {error_message} (код: {error_code})")
                raise Exception(f"HeyGen API limit exceeded: {error_message} (code: {error_code})")
            
            response.raise_for_status()
            result = response.json()
            
            # Логируем полный ответ HeyGen для диагностики
            logger.info(f"Полный ответ HeyGen API: {result}")
            
            normalized = normalize_create_video_response(result)
            logger.info(f"Видео создано успешно: {normalized['video_id']}")
            return normalized
            
        except requests.exceptions.HTTPError as e:
            # Обрабатываем HTTP ошибки (400, 500 и т.д.)
            logger.error(f"HTTP ошибка HeyGen API: {e.response.status_code} - {e.response.text}")
            raise Exception(f"HeyGen API HTTP error: {e.response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка HeyGen API при создании видео: {str(e)}")
            raise Exception(f"HeyGen API error: {str(e)}")
    
    def get_video_status(self, video_id: str) -> Dict[str, Any]:
        """
        Проверяет статус генерации видео с детальной обработкой ошибок
        
        Args:
            video_id: ID видео для проверки
            
        Returns:
            Dict с информацией о статусе видео, включая детали ошибок
        """
        try:
            from backend.config import settings
            response = self.client.get(f"/v1/video_status.get?video_id={video_id}", timeout=settings.HEYGEN_STATUS_TIMEOUT)
            
            # Проверяем статус ответа
            if response.status_code == 404:
                try:
                    error_data = response.json()
                    error_message = error_data.get("message", "Видео не найдено в системе HeyGen")
                    error_code = error_data.get("code", "404")
                except:
                    error_message = "Видео не найдено в системе HeyGen"
                    error_code = "404"
                
                logger.warning(f"Видео {video_id} не найдено в HeyGen: {error_message}")
                return {
                    "status": "not_found",
                    "error": error_message,
                    "error_code": error_code,
                    "video_id": video_id
                }
            
            response.raise_for_status()
            result = response.json()
            
            # Логируем полный ответ для диагностики
            logger.debug(f"Ответ HeyGen API для видео {video_id}: {result}")
            
            normalized = normalize_status_response(result, video_id)
            if normalized.get("status") == "generating":
                progress = normalized.get("progress", 0)
                logger.info(f"Видео {video_id} генерируется, прогресс: {progress}%")
            elif normalized.get("status") == "completed":
                logger.info(f"✅ Видео {video_id} готово")
            elif normalized.get("status") == "failed":
                logger.error(
                    f"HeyGen ошибка для видео {video_id}: {normalized.get('error')} (код: {normalized.get('error_code')})"
                )
            else:
                logger.warning(
                    f"Неизвестный статус для видео {video_id}: {normalized.get('status')}"
                )
            return normalized
            
        except requests.exceptions.Timeout:
            logger.error(f"Таймаут при проверке статуса видео {video_id}")
            return {
                "status": "timeout",
                "error": "Таймаут при проверке статуса видео",
                "video_id": video_id
            }
        except requests.exceptions.ConnectionError:
            logger.error(f"Ошибка подключения при проверке статуса видео {video_id}")
            return {
                "status": "connection_error",
                "error": "Ошибка подключения к HeyGen API",
                "video_id": video_id
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при проверке статуса видео {video_id}: {str(e)}")
            return {
                "status": "api_error",
                "error": f"Ошибка HeyGen API: {str(e)}",
                "video_id": video_id
            }
        except Exception as e:
            logger.error(f"Неожиданная ошибка при проверке статуса видео {video_id}: {str(e)}")
            return {
                "status": "unknown_error",
                "error": f"Неожиданная ошибка: {str(e)}",
                "video_id": video_id
            }
    
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
            from backend.config import settings
            response = self.client.stream(f"/v1/video/{video_id}/download", timeout=settings.HEYGEN_DOWNLOAD_TIMEOUT)
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
            from backend.config import settings
            response = self.client.get("/v2/avatars", timeout=settings.HEYGEN_STATUS_TIMEOUT)
            
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
            from backend.config import settings
            response = self.client.get("/v1/voice.list", timeout=settings.HEYGEN_STATUS_TIMEOUT)
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
                          avatar_id: str = "Abigail_expressive_2024112501",
                          voice_id: str = "9799f1ba6acd4b2b993fe813a18f9a91") -> Dict[str, Any]:
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
