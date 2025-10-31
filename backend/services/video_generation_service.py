"""
Обновленный сервис генерации с интеграцией HeyGen для создания видео-контента
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from backend.config import settings

from .mock_heygen_service import AdaptiveHeyGenService
from .generation_service import GenerationService

logger = logging.getLogger(__name__)

class VideoGenerationService:
    """Сервис для генерации уроков с видео-контентом"""
    
    def __init__(self):
        self.generation_service = GenerationService()
        self.heygen_service = AdaptiveHeyGenService()
        
        # Настройки по умолчанию для видео
        self.default_avatar_id = settings.HEYGEN_DEFAULT_AVATAR_ID
        self.default_voice_id = settings.HEYGEN_DEFAULT_VOICE_ID
        
        logger.info("VideoGenerationService инициализирован")
    
    async def generate_lesson_with_slide_videos(self, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует урок с видео для каждого слайда
        
        Args:
            lesson_data: Данные для генерации урока
            
        Returns:
            Dict с полным контентом урока включая видео для каждого слайда
        """
        try:
            logger.info(f"Начало генерации урока с видео для слайдов: {lesson_data.get('title', 'Без названия')}")
            
            # 1. Создаем базовый контент урока
            lesson_content = self._create_basic_lesson_content(lesson_data)
            
            # 2. Разбиваем контент на слайды
            slides = self._split_content_to_slides(lesson_content)
            
            # 3. Создаем видео для каждого слайда
            slide_videos = []
            for i, slide in enumerate(slides):
                logger.info(f"Создание видео для слайда {i+1}/{len(slides)}")
                
                video_config = self._prepare_slide_video_config(slide, lesson_data, i+1)
                video_info = await self._create_slide_video(video_config)
                
                slide_videos.append({
                    'slide_number': i+1,
                    'slide_title': slide.get('title', f'Слайд {i+1}'),
                    'slide_content': slide.get('content', ''),
                    'video': video_info
                })
            
            # 4. Добавляем информацию о видео к контенту урока
            lesson_content['slides'] = slide_videos
            lesson_content['total_slides'] = len(slides)
            
            # 5. Сохраняем метаданные
            lesson_content['metadata'] = {
                'generated_at': datetime.now().isoformat(),
                'video_enabled': True,
                'video_type': 'per_slide',
                'avatar_id': lesson_data.get('avatar_id', self.default_avatar_id),
                'voice_id': lesson_data.get('voice_id', self.default_voice_id)
            }
            
            logger.info(f"Урок с видео для слайдов успешно сгенерирован: {lesson_content.get('title')}")
            return lesson_content
            
        except Exception as e:
            logger.error(f"Ошибка при генерации урока с видео для слайдов: {str(e)}")
            raise Exception(f"Error generating lesson with slide videos: {str(e)}")
    
    def _split_content_to_slides(self, lesson_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Разбивает контент урока на слайды
        
        Args:
            lesson_content: Контент урока
            
        Returns:
            List со слайдами
        """
        content = lesson_content.get('content', '')
        
        # Простое разбиение по абзацам (можно улучшить)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        slides = []
        for i, paragraph in enumerate(paragraphs):
            slides.append({
                'title': f"Слайд {i+1}",
                'content': paragraph,
                'slide_number': i+1
            })
        
        # Если контент короткий, создаем один слайд
        if not slides:
            slides = [{
                'title': 'Основной слайд',
                'content': content,
                'slide_number': 1
            }]
        
        return slides
    
    def _prepare_slide_video_config(self, slide: Dict[str, Any], lesson_data: Dict[str, Any], slide_number: int) -> Dict[str, Any]:
        """
        Подготавливает конфигурацию для создания видео слайда
        
        Args:
            slide: Данные слайда
            lesson_data: Исходные данные урока
            slide_number: Номер слайда
            
        Returns:
            Dict с конфигурацией для видео слайда
        """
        return {
            'title': f"{lesson_data.get('title', 'Урок')} - Слайд {slide_number}",
            'content': slide.get('content', ''),
            'slide_number': slide_number,
            'avatar_id': lesson_data.get('avatar_id', self.default_avatar_id),
            'voice_id': lesson_data.get('voice_id', self.default_voice_id),
            'language': lesson_data.get('language', 'ru'),
            'background_id': lesson_data.get('background_id'),
            'quality': lesson_data.get('quality', 'low'),
            'test_mode': lesson_data.get('test_mode', True)
        }
    
    async def _create_slide_video(self, video_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создает видео для слайда
        
        Args:
            video_config: Конфигурация для видео
            
        Returns:
            Dict с информацией о созданном видео
        """
        try:
            # Создаем видео через HeyGen
            video_response = self.heygen_service.create_video_from_text(
                text=video_config['content'],
                avatar_id=video_config['avatar_id'],
                voice_id=video_config['voice_id'],
                quality=video_config.get('quality', 'low'),
                test_mode=video_config.get('test_mode', True)
            )
            
            return {
                'video_id': video_response.get('data', {}).get('video_id'),
                'status': 'processing',
                'created_at': datetime.now().isoformat(),
                'slide_number': video_config['slide_number'],
                'title': video_config['title']
            }
            
        except Exception as e:
            logger.error(f"Ошибка при создании видео для слайда {video_config['slide_number']}: {str(e)}")
            return {
                'video_id': None,
                'status': 'error',
                'error': str(e),
                'slide_number': video_config['slide_number'],
                'title': video_config['title']
            }
    
    def _create_basic_lesson_content(self, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создает базовый контент урока
        
        Args:
            lesson_data: Данные для генерации урока
            
        Returns:
            Dict с базовым контентом урока
        """
        return {
            'title': lesson_data.get('title', 'Урок'),
            'description': lesson_data.get('description', 'Описание урока'),
            'content': lesson_data.get('text', 'Содержание урока'),
            'duration': lesson_data.get('duration', '10 минут'),
            'difficulty': lesson_data.get('difficulty', 'Начальный')
        }
    
    async def generate_lesson_with_video(self, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует урок с видео-контентом
        
        Args:
            lesson_data: Данные для генерации урока
            
        Returns:
            Dict с полным контентом урока включая видео
        """
        try:
            logger.info(f"Начало генерации урока с видео: {lesson_data.get('title', 'Без названия')}")
            
            # 1. Создаем базовый контент урока
            lesson_content = self._create_basic_lesson_content(lesson_data)
            
            # 2. Подготавливаем данные для видео
            video_config = self._prepare_video_config(lesson_data, lesson_content)
            
            # 3. Создаем видео через HeyGen
            video_info = await self._create_lesson_video(video_config)
            
            # 4. Проверяем статус создания видео
            if video_info.get('status') == 'failed':
                logger.error(f"Не удалось создать видео для урока: {video_info.get('error')}")
                lesson_content['video'] = video_info
                lesson_content['metadata'] = {
                    'generated_at': datetime.now().isoformat(),
                    'video_enabled': False,
                    'video_error': video_info.get('error'),
                    'avatar_id': video_config.get('avatar_id'),
                    'voice_id': video_config.get('voice_id')
                }
                return lesson_content
            
            # 5. Добавляем информацию о видео к контенту урока
            lesson_content['video'] = video_info
            
            # 6. Сохраняем метаданные
            lesson_content['metadata'] = {
                'generated_at': datetime.now().isoformat(),
                'video_enabled': True,
                'avatar_id': video_config.get('avatar_id'),
                'voice_id': video_config.get('voice_id')
            }
            
            logger.info(f"Урок с видео успешно сгенерирован: {lesson_content.get('title')}")
            return lesson_content
            
        except Exception as e:
            logger.error(f"Ошибка при генерации урока с видео: {str(e)}")
            raise Exception(f"Error generating lesson with video: {str(e)}")
    
    def _prepare_video_config(self, lesson_data: Dict[str, Any], lesson_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Подготавливает конфигурацию для создания видео
        
        Args:
            lesson_data: Исходные данные урока
            lesson_content: Сгенерированный контент урока
            
        Returns:
            Dict с конфигурацией для видео
        """
        return {
            'title': lesson_content.get('title', 'Урок'),
            'content': lesson_data.get('content', ''),  # Используем оригинальный контент из lesson_data
            'introduction': lesson_content.get('introduction', ''),
            'conclusion': lesson_content.get('conclusion', ''),
            'avatar_id': lesson_data.get('avatar_id', self.default_avatar_id),
            'voice_id': lesson_data.get('voice_id', self.default_voice_id),
            'language': lesson_data.get('language', 'ru'),
            'background_id': lesson_data.get('background_id')
        }
    
    async def _create_lesson_video(self, video_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создает видео для урока
        
        Args:
            video_config: Конфигурация для видео
            
        Returns:
            Dict с информацией о созданном видео
        """
        try:
            # Создаем видео через HeyGen
            video_response = self.heygen_service.create_lesson_video(
                lesson_title=video_config['title'],
                lesson_content=video_config['content'],
                avatar_id=video_config['avatar_id'],
                voice_id=video_config['voice_id']
            )
            
            # Проверяем, что видео действительно создано
            if not video_response.get('video_id'):
                raise Exception("HeyGen не вернул video_id")
            
            return {
                'video_id': video_response['video_id'],
                'script': video_response.get('script', ''),
                'status': 'generating',
                'created_at': video_response.get('created_at', ''),
                'avatar_id': video_config['avatar_id'],
                'voice_id': video_config['voice_id']
            }
            
        except Exception as e:
            logger.error(f"Ошибка при создании видео: {str(e)}")
            # Возвращаем информацию об ошибке вместо исключения
            return {
                'video_id': None,
                'script': '',
                'status': 'failed',
                'error': str(e),
                'created_at': '',
                'avatar_id': video_config['avatar_id'],
                'voice_id': video_config['voice_id']
            }
    
    async def check_video_status(self, video_id: str) -> Dict[str, Any]:
        """
        Проверяет статус генерации видео
        
        Args:
            video_id: ID видео для проверки
            
        Returns:
            Dict с информацией о статусе
        """
        try:
            status = self.heygen_service.get_video_status(video_id)

            # Нормализуем возможные поля статуса от разных реализаций
            raw_status = (
                status.get('status') or 
                status.get('task_status') or 
                status.get('state') or 
                'unknown'
            )
            # Нормализуем промежуточные статусы в 'generating'
            if str(raw_status).lower() in ['processing', 'in_progress', 'queued', 'pending', 'working']:
                raw_status = 'generating'
            raw_progress = (
                status.get('progress') or 
                status.get('percent') or 
                status.get('percentage') or 
                0
            )
            # Приводим прогресс к 0..100
            try:
                if isinstance(raw_progress, float):
                    # если 0..1 — конвертируем в проценты
                    raw_progress = int(raw_progress * 100) if 0 <= raw_progress <= 1 else int(raw_progress)
                elif isinstance(raw_progress, str):
                    raw_progress = int(float(raw_progress))
            except Exception:
                raw_progress = 0

            result = {
                'video_id': video_id,
                'status': raw_status,
                'progress': max(0, min(100, raw_progress)),
                'download_url': status.get('download_url') or status.get('video_url') or status.get('url'),
                'error': status.get('error') or status.get('message'),
                'error_code': status.get('error_code'),
                'error_details': status.get('error_details'),
                'duration': status.get('duration'),
                'file_size': status.get('file_size'),
                'created_at': status.get('created_at'),
                'estimated_time': status.get('estimated_time') or status.get('eta')
            }
            
            logger.info(f"Статус видео {video_id}: {result['status']}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при проверке статуса видео {video_id}: {str(e)}")
            return {
                'video_id': video_id,
                'status': 'unknown_error',
                'error': f'Ошибка проверки статуса: {str(e)}',
                'progress': 0
            }
    
    async def wait_for_video_completion(self, video_id: str, max_wait_time: int = 300) -> Dict[str, Any]:
        """
        Ожидает завершения генерации видео
        
        Args:
            video_id: ID видео
            max_wait_time: Максимальное время ожидания в секундах
            
        Returns:
            Dict с финальным статусом
        """
        try:
            final_status = self.heygen_service.wait_for_video_completion(video_id, max_wait_time)
            return {
                'video_id': video_id,
                'status': 'completed',
                'download_url': final_status.get('download_url'),
                'duration': final_status.get('duration'),
                'file_size': final_status.get('file_size')
            }
        except Exception as e:
            logger.error(f"Ошибка при ожидании завершения видео {video_id}: {str(e)}")
            return {
                'video_id': video_id,
                'status': 'error',
                'error_message': str(e)
            }
    
    async def download_video(self, video_id: str, output_path: str) -> bool:
        """
        Скачивает готовое видео
        
        Args:
            video_id: ID видео
            output_path: Путь для сохранения
            
        Returns:
            True если успешно
        """
        try:
            return self.heygen_service.download_video(video_id, output_path)
        except Exception as e:
            logger.error(f"Ошибка при скачивании видео {video_id}: {str(e)}")
            return False
    
    async def get_available_avatars(self) -> List[Dict[str, Any]]:
        """
        Получает список доступных аватаров
        
        Returns:
            List с информацией об аватарах
        """
        try:
            avatars_response = self.heygen_service.get_available_avatars()
            return avatars_response.get('data', [])
        except Exception as e:
            logger.error(f"Ошибка при получении аватаров: {str(e)}")
            return []
    
    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """
        Получает список доступных голосов
        
        Returns:
            List с информацией о голосах
        """
        try:
            voices_response = self.heygen_service.get_available_voices()
            data = voices_response.get('data', {})
            
            # Проверяем разные варианты структуры ответа
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                # Если data - это объект с полем list
                if 'list' in data and isinstance(data['list'], list):
                    return data['list']
                # Если data - это объект с полем voices
                elif 'voices' in data and isinstance(data['voices'], list):
                    return data['voices']
            
            return []
        except Exception as e:
            logger.error(f"Ошибка при получении голосов: {str(e)}")
            return []
    
    async def generate_course_videos(self, course_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Генерирует видео для всего курса
        
        Args:
            course_data: Данные курса с уроками
            
        Returns:
            Dict с информацией о созданных видео
        """
        try:
            logger.info(f"Начало генерации видео для курса: {course_data.get('title', 'Без названия')}")
            
            course_videos = {
                'course_id': course_data.get('id'),
                'course_title': course_data.get('title'),
                'lessons': [],
                'generated_at': datetime.now().isoformat()
            }
            
            lessons = course_data.get('lessons', [])
            
            for lesson in lessons:
                try:
                    # Генерируем видео для каждого урока
                    lesson_with_video = await self.generate_lesson_with_video(lesson)
                    course_videos['lessons'].append({
                        'lesson_id': lesson.get('id'),
                        'lesson_title': lesson.get('title'),
                        'video_id': lesson_with_video.get('video', {}).get('video_id'),
                        'status': 'generating'
                    })
                    
                    logger.info(f"Видео для урока '{lesson.get('title')}' поставлено в очередь")
                    
                except Exception as e:
                    logger.error(f"Ошибка при генерации видео для урока {lesson.get('title')}: {str(e)}")
                    course_videos['lessons'].append({
                        'lesson_id': lesson.get('id'),
                        'lesson_title': lesson.get('title'),
                        'error': str(e),
                        'status': 'error'
                    })
            
            logger.info(f"Генерация видео для курса завершена: {len(course_videos['lessons'])} уроков")
            return course_videos
            
        except Exception as e:
            logger.error(f"Ошибка при генерации видео для курса: {str(e)}")
            raise Exception(f"Error generating course videos: {str(e)}")
    
    def _optimize_script_for_video(self, content: str, max_length: int = 2000) -> str:
        """
        Оптимизирует скрипт для видео (ограничивает длину)
        
        Args:
            content: Исходный контент
            max_length: Максимальная длина скрипта
            
        Returns:
            Оптимизированный скрипт
        """
        if len(content) <= max_length:
            return content
        
        # Разбиваем на предложения и берем первые
        sentences = content.split('. ')
        optimized_content = ""
        
        for sentence in sentences:
            if len(optimized_content + sentence + '. ') <= max_length:
                optimized_content += sentence + '. '
            else:
                break
        
        return optimized_content.rstrip()
