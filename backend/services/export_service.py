"""
Сервис‑фасад для экспорта контента в разные форматы (Markdown, HTML, PPTX).

Используемые модули:
- `backend.services.export.markdown/html/pptx` — специализированные провайдеры
  форматов. Этот сервис делегирует туда фактическую генерацию.
- `logging` — журналирование операций экспорта.
"""
from typing import Dict, Any
from io import BytesIO
import logging

from backend.models.domain import Course, Module
from backend.services.export.markdown import (
    export_course_markdown as _export_course_markdown,
    export_course_text as _export_course_text,
    export_module_markdown as _export_module_markdown,
    export_lesson_markdown as _export_lesson_markdown,
)
from backend.services.export.html import (
    export_course_html as _export_course_html,
    export_module_html as _export_module_html,
    export_lesson_html as _export_lesson_html,
)
from backend.services.export.pptx import (
    export_course_pptx as _export_course_pptx,
    export_module_pptx as _export_module_pptx,
    export_lesson_pptx as _export_lesson_pptx,
)
from backend.services.export.scorm import (
    export_course_scorm as _export_course_scorm,
    SCORM_VERSION_12,
)

logger = logging.getLogger(__name__)


class ExportService:
    """Экспорт курсов, модулей и уроков в различные форматы.

    Методы возвращают строку (для текстовых форматов) или байты (для PPTX).
    На уровне API эти значения упаковываются в `fastapi.Response`.
    """
    
    # ========== ЭКСПОРТ КУРСА ==========
    
    @staticmethod
    def export_course_markdown(course: Course, course_id: int = None) -> str:
        """Генерирует полный Markdown для всего курса с детальным контентом.

        При наличии course_id подтягивает из БД слайды и тесты
        (аналогично SCORM, но без видео).
        """
        return _export_course_markdown(course, course_id=course_id)
    
    @staticmethod
    def export_course_text(course: Course) -> str:
        """Генерирует простой текст для всего курса"""
        return _export_course_text(course)
    
    @staticmethod
    def export_course_html(course: Course) -> str:
        """Генерирует HTML представление курса"""
        return _export_course_html(course)
    
    @staticmethod
    def export_course_pptx(course: Course) -> bytes:
        """Генерирует PPTX (презентацию) для курса"""
        return _export_course_pptx(course)
    
    @staticmethod
    def export_course_scorm(
        course: Course,
        course_id: int,
        include_videos: bool = False,
        scorm_version: str = SCORM_VERSION_12,
        single_sco: bool = False,
    ) -> bytes:
        """Генерирует SCORM пакет (ZIP архив) для курса"""
        return _export_course_scorm(
            course, course_id, include_videos, scorm_version, single_sco
        )
    
    # ========== ЭКСПОРТ МОДУЛЯ (ДЕТАЛЬНЫЙ КОНТЕНТ) ==========
    
    @staticmethod
    def export_module_markdown(course: Course, module: Module, content_data: dict) -> str:
        """Markdown экспорт детального контента модуля"""
        return _export_module_markdown(course, module, content_data)
    
    @staticmethod  
    def export_module_html(course: Course, module: Module, content_data: dict) -> str:
        """HTML экспорт детального контента модуля"""
        return _export_module_html(course, module, content_data)
    
    @staticmethod
    def export_module_pptx(course: Course, module: Module, content_data: dict) -> bytes:
        """PPTX экспорт детального контента модуля"""
        return _export_module_pptx(course, module, content_data)
    
    # ========== ЭКСПОРТ УРОКА (ДЕТАЛЬНЫЙ КОНТЕНТ) ==========
    
    @staticmethod
    def export_lesson_markdown(course: Course, module: Module, lesson, content_data: dict) -> str:
        """Markdown экспорт детального контента урока"""
        return _export_lesson_markdown(course, module, lesson, content_data)
    
    @staticmethod
    def export_lesson_html(course: Course, module: Module, lesson, content_data: dict) -> str:
        """HTML экспорт детального контента урока"""
        return _export_lesson_html(course, module, lesson, content_data)
    
    @staticmethod
    def export_lesson_pptx(course: Course, module: Module, lesson, content_data: dict) -> bytes:
        """PPTX экспорт детального контента урока"""
        return _export_lesson_pptx(course, module, lesson, content_data)


# Глобальный экземпляр
export_service = ExportService()

