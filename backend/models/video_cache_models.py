"""
Модели для хранения информации о сгенерированных видео
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class VideoCache(BaseModel):
    """Модель для кэширования информации о видео"""
    video_id: str
    lesson_key: str  # Уникальный ключ урока (course_id_module_number_lesson_index)
    title: str
    content: str
    avatar_id: str
    voice_id: str
    language: str
    quality: str
    status: str  # completed, failed, generating
    download_url: Optional[str] = None
    duration: Optional[int] = None
    file_size: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
    error_code: Optional[str] = None

class VideoGenerationRequest(BaseModel):
    """Модель для запроса генерации видео"""
    title: str
    content: str
    avatar_id: str
    voice_id: str
    language: str = "ru"
    quality: str = "low"
    regenerate: bool = False  # Флаг для принудительной перегенерации

class VideoGenerationResponse(BaseModel):
    """Модель для ответа генерации видео"""
    success: bool
    video_id: Optional[str] = None
    status: str
    message: str
    is_cached: bool = False  # Флаг, что видео взято из кэша
    download_url: Optional[str] = None
    error: Optional[str] = None
