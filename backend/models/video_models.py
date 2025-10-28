"""
Обновленные модели данных для поддержки видео-контента
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class VideoStatus(str, Enum):
    """Статусы генерации видео"""
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    PENDING = "pending"

class AvatarConfig(BaseModel):
    """Конфигурация аватара для видео"""
    avatar_id: str = Field(..., description="ID аватара HeyGen")
    avatar_style: str = Field(default="normal", description="Стиль аватара")
    background_id: Optional[str] = Field(None, description="ID фона")

class VoiceConfig(BaseModel):
    """Конфигурация голоса для видео"""
    voice_id: str = Field(..., description="ID голоса HeyGen")
    language: str = Field(default="ru", description="Язык озвучивания")
    speed: float = Field(default=1.0, description="Скорость речи")

class VideoMetadata(BaseModel):
    """Метаданные видео"""
    video_id: str = Field(..., description="ID видео в HeyGen")
    status: VideoStatus = Field(default=VideoStatus.PENDING, description="Статус генерации")
    script: str = Field(..., description="Скрипт для видео")
    avatar_config: AvatarConfig = Field(..., description="Конфигурация аватара")
    voice_config: VoiceConfig = Field(..., description="Конфигурация голоса")
    created_at: datetime = Field(default_factory=datetime.now, description="Время создания")
    completed_at: Optional[datetime] = Field(None, description="Время завершения")
    download_url: Optional[str] = Field(None, description="URL для скачивания")
    duration: Optional[int] = Field(None, description="Длительность в секундах")
    file_size: Optional[int] = Field(None, description="Размер файла в байтах")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")

class LessonVideo(BaseModel):
    """Видео для урока"""
    video_metadata: VideoMetadata = Field(..., description="Метаданные видео")
    is_enabled: bool = Field(default=True, description="Включено ли видео")
    auto_generate: bool = Field(default=True, description="Автоматическая генерация")

class LessonCreateWithVideo(BaseModel):
    """Создание урока с видео"""
    title: str = Field(..., description="Название урока")
    description: str = Field(..., description="Описание урока")
    content: str = Field(..., description="Содержание урока")
    module_id: int = Field(..., description="ID модуля")
    order: int = Field(..., description="Порядок в модуле")
    duration_minutes: int = Field(default=30, description="Длительность в минутах")
    
    # Настройки видео
    video_enabled: bool = Field(default=True, description="Включить видео")
    avatar_id: str = Field(default="default", description="ID аватара")
    voice_id: str = Field(default="default", description="ID голоса")
    language: str = Field(default="ru", description="Язык озвучивания")
    background_id: Optional[str] = Field(None, description="ID фона")

class LessonUpdateWithVideo(BaseModel):
    """Обновление урока с видео"""
    title: Optional[str] = Field(None, description="Название урока")
    description: Optional[str] = Field(None, description="Описание урока")
    content: Optional[str] = Field(None, description="Содержание урока")
    order: Optional[int] = Field(None, description="Порядок в модуле")
    duration_minutes: Optional[int] = Field(None, description="Длительность в минутах")
    
    # Настройки видео
    video_enabled: Optional[bool] = Field(None, description="Включить видео")
    avatar_id: Optional[str] = Field(None, description="ID аватара")
    voice_id: Optional[str] = Field(None, description="ID голоса")
    language: Optional[str] = Field(None, description="Язык озвучивания")
    background_id: Optional[str] = Field(None, description="ID фона")
    regenerate_video: bool = Field(default=False, description="Пересоздать видео")

class CourseCreateWithVideo(BaseModel):
    """Создание курса с видео"""
    title: str = Field(..., description="Название курса")
    description: str = Field(..., description="Описание курса")
    target_audience: str = Field(..., description="Целевая аудитория")
    duration_hours: int = Field(..., description="Длительность в часах")
    
    # Настройки видео по умолчанию для всего курса
    default_avatar_id: str = Field(default="default", description="ID аватара по умолчанию")
    default_voice_id: str = Field(default="default", description="ID голоса по умолчанию")
    default_language: str = Field(default="ru", description="Язык по умолчанию")
    video_enabled: bool = Field(default=True, description="Включить видео для всех уроков")

class CourseUpdateWithVideo(BaseModel):
    """Обновление курса с видео"""
    title: Optional[str] = Field(None, description="Название курса")
    description: Optional[str] = Field(None, description="Описание курса")
    target_audience: Optional[str] = Field(None, description="Целевая аудитория")
    duration_hours: Optional[int] = Field(None, description="Длительность в часах")
    
    # Настройки видео
    default_avatar_id: Optional[str] = Field(None, description="ID аватара по умолчанию")
    default_voice_id: Optional[str] = Field(None, description="ID голоса по умолчанию")
    default_language: Optional[str] = Field(None, description="Язык по умолчанию")
    video_enabled: Optional[bool] = Field(None, description="Включить видео для всех уроков")
    regenerate_all_videos: bool = Field(default=False, description="Пересоздать все видео")

class VideoGenerationRequest(BaseModel):
    """Запрос на генерацию видео"""
    lesson_id: int = Field(..., description="ID урока")
    title: str = Field(..., description="Название урока")
    content: str = Field(..., description="Содержание урока")
    avatar_id: str = Field(default="default", description="ID аватара")
    voice_id: str = Field(default="default", description="ID голоса")
    language: str = Field(default="ru", description="Язык озвучивания")
    background_id: Optional[str] = Field(None, description="ID фона")

class VideoGenerationResponse(BaseModel):
    """Ответ на запрос генерации видео"""
    success: bool = Field(..., description="Успешность операции")
    video_id: Optional[str] = Field(None, description="ID созданного видео")
    status: VideoStatus = Field(..., description="Статус генерации")
    message: str = Field(..., description="Сообщение")
    estimated_completion_time: Optional[int] = Field(None, description="Ожидаемое время завершения в секундах")

class VideoStatusResponse(BaseModel):
    """Ответ с статусом видео"""
    video_id: str = Field(..., description="ID видео")
    status: VideoStatus = Field(..., description="Статус генерации")
    progress: Optional[int] = Field(None, description="Прогресс в процентах")
    download_url: Optional[str] = Field(None, description="URL для скачивания")
    error_message: Optional[str] = Field(None, description="Сообщение об ошибке")
    duration: Optional[int] = Field(None, description="Длительность в секундах")
    file_size: Optional[int] = Field(None, description="Размер файла в байтах")

class BatchVideoStatusResponse(BaseModel):
    """Ответ с статусами нескольких видео"""
    videos: List[VideoStatusResponse] = Field(..., description="Список статусов видео")
    total: int = Field(..., description="Общее количество видео")
    completed: int = Field(..., description="Количество завершенных")
    failed: int = Field(..., description="Количество неудачных")
    generating: int = Field(..., description="Количество генерирующихся")

class AvatarInfo(BaseModel):
    """Информация об аватаре"""
    avatar_id: str = Field(..., description="ID аватара")
    name: str = Field(..., description="Название аватара")
    description: Optional[str] = Field(None, description="Описание аватара")
    gender: Optional[str] = Field(None, description="Пол аватара")
    age_range: Optional[str] = Field(None, description="Возрастной диапазон")
    preview_url: Optional[str] = Field(None, description="URL превью")

class VoiceInfo(BaseModel):
    """Информация о голосе"""
    voice_id: str = Field(..., description="ID голоса")
    name: str = Field(..., description="Название голоса")
    language: str = Field(..., description="Язык")
    gender: Optional[str] = Field(None, description="Пол")
    age_range: Optional[str] = Field(None, description="Возрастной диапазон")
    accent: Optional[str] = Field(None, description="Акцент")
    preview_url: Optional[str] = Field(None, description="URL превью")

class VideoConfig(BaseModel):
    """Конфигурация для видео"""
    avatar: AvatarInfo = Field(..., description="Информация об аватаре")
    voice: VoiceInfo = Field(..., description="Информация о голосе")
    language: str = Field(default="ru", description="Язык озвучивания")
    background_id: Optional[str] = Field(None, description="ID фона")
    quality: str = Field(default="high", description="Качество видео")
    aspect_ratio: str = Field(default="16:9", description="Соотношение сторон")

class LessonWithVideo(BaseModel):
    """Урок с видео-контентом"""
    id: int = Field(..., description="ID урока")
    title: str = Field(..., description="Название урока")
    description: str = Field(..., description="Описание урока")
    content: str = Field(..., description="Содержание урока")
    module_id: int = Field(..., description="ID модуля")
    order: int = Field(..., description="Порядок в модуле")
    duration_minutes: int = Field(..., description="Длительность в минутах")
    
    # Видео-контент
    video: Optional[LessonVideo] = Field(None, description="Видео урока")
    video_enabled: bool = Field(default=True, description="Включено ли видео")
    
    # Метаданные
    created_at: datetime = Field(..., description="Время создания")
    updated_at: datetime = Field(..., description="Время обновления")

class CourseWithVideo(BaseModel):
    """Курс с видео-контентом"""
    id: int = Field(..., description="ID курса")
    title: str = Field(..., description="Название курса")
    description: str = Field(..., description="Описание курса")
    target_audience: str = Field(..., description="Целевая аудитория")
    duration_hours: int = Field(..., description="Длительность в часах")
    
    # Настройки видео
    video_enabled: bool = Field(default=True, description="Включено ли видео")
    default_avatar_id: str = Field(default="default", description="ID аватара по умолчанию")
    default_voice_id: str = Field(default="default", description="ID голоса по умолчанию")
    default_language: str = Field(default="ru", description="Язык по умолчанию")
    
    # Уроки с видео
    lessons: List[LessonWithVideo] = Field(default=[], description="Уроки курса")
    
    # Статистика видео
    total_lessons: int = Field(default=0, description="Общее количество уроков")
    videos_generated: int = Field(default=0, description="Количество сгенерированных видео")
    videos_completed: int = Field(default=0, description="Количество завершенных видео")
    videos_failed: int = Field(default=0, description="Количество неудачных видео")
    
    # Метаданные
    created_at: datetime = Field(..., description="Время создания")
    updated_at: datetime = Field(..., description="Время обновления")
