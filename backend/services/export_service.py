"""
Сервис для экспорта контента в различные форматы
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

logger = logging.getLogger(__name__)


class ExportService:
    """Сервис для экспорта курсов, модулей и уроков в различные форматы"""
    
    # ========== ЭКСПОРТ КУРСА ==========
    
    @staticmethod
    def export_course_markdown(course: Course) -> str:
        """Генерирует Markdown для всего курса"""
        return _export_course_markdown(course)
    
    @staticmethod
    def export_course_text(course: Course) -> str:
        return _export_course_text(course)
    
    @staticmethod
    def export_course_html(course: Course) -> str:
        return _export_course_html(course)
    
    @staticmethod
    def export_course_pptx(course: Course) -> bytes:
        return _export_course_pptx(course)
    
    # ========== ЭКСПОРТ МОДУЛЯ (ДЕТАЛЬНЫЙ КОНТЕНТ) ==========
    
    @staticmethod
    def export_module_markdown(course: Course, module: Module, content_data: dict) -> str:
        return _export_module_markdown(course, module, content_data)
    
    @staticmethod  
    def export_module_html(course: Course, module: Module, content_data: dict) -> str:
        return _export_module_html(course, module, content_data)
    
    @staticmethod
    def export_module_pptx(course: Course, module: Module, content_data: dict) -> bytes:
        return _export_module_pptx(course, module, content_data)
    
    # ========== ЭКСПОРТ УРОКА (ДЕТАЛЬНЫЙ КОНТЕНТ) ==========
    
    @staticmethod
    def export_lesson_markdown(course: Course, module: Module, lesson, content_data: dict) -> str:
        return _export_lesson_markdown(course, module, lesson, content_data)
    
    @staticmethod
    def export_lesson_html(course: Course, module: Module, lesson, content_data: dict) -> str:
        return _export_lesson_html(course, module, lesson, content_data)
    
    @staticmethod
    def export_lesson_pptx(course: Course, module: Module, lesson, content_data: dict) -> bytes:
        return _export_lesson_pptx(course, module, lesson, content_data)


# Глобальный экземпляр
export_service = ExportService()

