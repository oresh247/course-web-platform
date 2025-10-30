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
            
            # Проверяем структуру ответа HeyGen
            video_id = None
            if result.get('data') and result['data'].get('video_id'):
                # Новая структура: {"data": {"video_id": "..."}}
                video_id = result['data']['video_id']
            elif result.get('video_id'):
                # Старая структура: {"video_id": "..."}
                video_id = result['video_id']
            
            # Проверяем реальный статус в ответе HeyGen
            if video_id is None:
                error_message = result.get('message', 'Неизвестная ошибка генерации')
                error_code = result.get('code', 'unknown')
                logger.error(f"HeyGen вернул ошибку при создании видео: {error_message} (код: {error_code})")
                logger.error(f"Полный ответ с ошибкой: {result}")
                raise Exception(f"HeyGen generation failed: {error_message} (code: {error_code})")
            
            logger.info(f"Видео создано успешно: {video_id}")
            
            # Возвращаем результат в стандартном формате
            return {
                'video_id': video_id,
                'script': result.get('data', {}).get('script', ''),
                'created_at': result.get('data', {}).get('created_at', ''),
                'status': result.get('data', {}).get('status', 'generating')
            }
            
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
            response = requests.get(
                f"{self.base_url}/v1/video_status.get?video_id={video_id}",
                headers=self.headers,
                timeout=10,
                verify=False
            )
            
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
            
            # Обрабатываем разные варианты структуры ответа HeyGen
            status = None
            progress = 0
            download_url = None
            error_details = None
            
            # Проверяем различные варианты структуры ответа
            if isinstance(result, dict):
                # Вариант 1: {"status": "...", "data": {...}}
                if "status" in result:
                    status = result.get("status")
                    data = result.get("data", {})
                    if isinstance(data, dict):
                        progress = data.get("progress", 0)
                        # HeyGen API возвращает URL в поле video_url при статусе completed
                        download_url = data.get("video_url") or data.get("videoUrl") or data.get("download_url") or data.get("downloadUrl")
                        if "error" in data:
                            error_details = data.get("error", {})
                # Вариант 2: {"data": {"status": "...", "progress": ...}}
                elif "data" in result:
                    data = result.get("data", {})
                    if isinstance(data, dict):
                        status = data.get("status")
                        progress = data.get("progress", 0)
                        # HeyGen API возвращает URL в поле video_url при статусе completed
                        download_url = data.get("video_url") or data.get("videoUrl") or data.get("download_url") or data.get("downloadUrl")
                        if "error" in data:
                            error_details = data.get("error", {})
                else:
                    # Прямая структура без вложенности
                    status = result.get("status")
                    progress = result.get("progress", 0)
                    # HeyGen API возвращает URL в поле video_url при статусе completed
                    download_url = result.get("video_url") or result.get("videoUrl") or result.get("download_url") or result.get("downloadUrl")
                    if "error" in result:
                        error_details = result.get("error", {})
            
            # Если статус не определен, но есть video_id, считаем что видео генерируется
            if not status and video_id:
                status = "generating"
                logger.info(f"Статус не определен для видео {video_id}, устанавливаем 'generating'")
            
            # Обрабатываем ошибки
            if status == "failed" or error_details:
                error_msg = "Неизвестная ошибка генерации"
                error_code = "unknown"
                if isinstance(error_details, dict):
                    error_msg = error_details.get("message", error_msg)
                    error_code = error_details.get("code", error_code)
                elif isinstance(error_details, str):
                    error_msg = error_details
                
                logger.error(f"HeyGen ошибка для видео {video_id}: {error_msg} (код: {error_code})")
                return {
                    "status": "failed",
                    "error": error_msg,
                    "error_code": error_code,
                    "error_details": error_details,
                    "video_id": video_id
                }
            
            # Обрабатываем статус generating
            if status == "generating":
                logger.info(f"Видео {video_id} генерируется, прогресс: {progress}%")
                return {
                    "status": "generating",
                    "progress": progress,
                    "video_id": video_id,
                    "estimated_time": result.get("estimated_time") or result.get("data", {}).get("estimated_time")
                }
            
            # Обрабатываем статус completed
            if status == "completed":
                # Сначала пытаемся получить download_url из ответа API
                if not download_url:
                    # Получаем data объект для глубокого поиска
                    data_obj = result.get("data", {})
                    if not isinstance(data_obj, dict):
                        data_obj = result if isinstance(result, dict) else {}
                    
                    # Проверяем все возможные варианты названий полей (video_url - приоритетный для HeyGen)
                    download_url = (
                        data_obj.get("video_url") or      # Приоритетный вариант по документации HeyGen
                        data_obj.get("videoUrl") or 
                        data_obj.get("download_url") or 
                        data_obj.get("downloadUrl") or
                        data_obj.get("url") or
                        data_obj.get("video_file_url") or
                        data_obj.get("video_file") or
                        result.get("video_url") or
                        result.get("videoUrl") or
                        result.get("download_url") or 
                        result.get("downloadUrl") or
                        result.get("url")
                    )
                
                # Если URL не найден в API, генерируем его на основе video_id
                # Для просмотра: https://app.heygen.com/videos/{video_id}
                # Для скачивания: https://resource2.heygen.ai/video/transcode/{video_id}/1280x720.mp4
                if not download_url and video_id:
                    # Используем URL для скачивания (можно использовать для просмотра и скачивания)
                    download_url = f"https://resource2.heygen.ai/video/transcode/{video_id}/1280x720.mp4"
                    logger.info(f"✅ URL для скачивания сгенерирован для видео {video_id}: {download_url}")
                elif download_url:
                    logger.info(f"✅ Видео {video_id} готово, download_url найден: {download_url}")
                else:
                    logger.warning(f"⚠️ Не удалось получить или сгенерировать URL для видео {video_id}")
                
                return {
                    "status": "completed",
                    "progress": 100,
                    "video_id": video_id,
                    "download_url": download_url,  # URL для просмотра/скачивания
                    "duration": result.get("duration") or (result.get("data", {}) if isinstance(result.get("data"), dict) else {}).get("duration"),
                    "file_size": result.get("file_size") or (result.get("data", {}) if isinstance(result.get("data"), dict) else {}).get("file_size")
                }
            
            # Если статус неизвестен, возвращаем то что получили
            logger.warning(f"Неизвестный статус для видео {video_id}: {status}, возвращаем полный ответ")
            return {
                "status": status or "unknown",
                "progress": progress,
                "video_id": video_id,
                "download_url": download_url,
                "raw_response": result  # Добавляем полный ответ для отладки
            }
            
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
