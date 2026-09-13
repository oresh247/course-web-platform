"""
Общие зависимости и синглтоны для видеомаршрутов (HeyGen, кэш, генерация).
Чтобы избежать дублирования инстансов при разбиении роутеров, держим их здесь.
"""
import logging

from ..services.video_generation_service import VideoGenerationService
from ..services.mock_heygen_service import AdaptiveHeyGenService
from ..services.video_cache_service import VideoCacheService


logger = logging.getLogger(__name__)

# Сервис координации генерации видео (асинхронные действия, оркестрация)
video_service = VideoGenerationService()

# Без HEYGEN_API_KEY AdaptiveHeyGenService использует мок, Course Brief от этого не зависит.
heygen_service = AdaptiveHeyGenService()

# Служба кэширования видео-результатов
video_cache_service = VideoCacheService()


