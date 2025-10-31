"""
Общие зависимости и синглтоны для видеомаршрутов (HeyGen, кэш, генерация).
Чтобы избежать дублирования инстансов при разбиении роутеров, держим их здесь.
"""
import logging

from ..services.video_generation_service import VideoGenerationService
from ..services.heygen_service import HeyGenService
from ..services.video_cache_service import VideoCacheService


logger = logging.getLogger(__name__)

# Сервис координации генерации видео (асинхронные действия, оркестрация)
video_service = VideoGenerationService()

# Принудительно используем реальный HeyGen клиент (для диагностики сети)
heygen_service = HeyGenService()

# Служба кэширования видео-результатов
video_cache_service = VideoCacheService()


