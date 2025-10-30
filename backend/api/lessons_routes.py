"""
API endpoints для работы с уроками курса
"""
from fastapi import APIRouter, HTTPException
import logging
import json

from backend.models.domain import Course
from backend.ai.content_generator import ContentGenerator
from backend.database import db
from backend.services.generation_service import generation_service
from backend.services.export_service import export_service
from backend.utils.formatters import safe_filename, format_content_disposition
from fastapi.responses import Response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/courses", tags=["lessons"])

# Инициализируем генератор контента
content_generator = ContentGenerator()


@router.post("/{course_id}/modules/{module_number}/lessons/{lesson_index}/regenerate-content", response_model=dict)
async def regenerate_lesson_content(course_id: int, module_number: int, lesson_index: int):
    """Регенерировать план контента урока с помощью AI"""
    try:
        course_data = db.get_course(course_id)
        if not course_data:
            raise HTTPException(status_code=404, detail="Курс не найден")
        
        course_data.pop('id', None)
        course_data.pop('created_at', None)
        course_data.pop('updated_at', None)
        course = Course(**course_data)
        
        module = None
        for m in course.modules:
            if m.module_number == module_number:
                module = m
                break
        
        if not module or lesson_index >= len(module.lessons):
            raise HTTPException(status_code=404, detail="Модуль или урок не найден")
        
        lesson = module.lessons[lesson_index]
        
        new_content_outline = generation_service.regenerate_lesson_content_outline(
            course_title=course.course_title,
            module_title=module.module_title,
            lesson_title=lesson.lesson_title,
            lesson_goal=lesson.lesson_goal,
            lesson_format=lesson.format,
            estimated_time_minutes=lesson.estimated_time_minutes
        )
        
        if not new_content_outline:
            raise HTTPException(status_code=500, detail="Не удалось регенерировать план контента")
        
        lesson.content_outline = new_content_outline
        db.update_course(course_id, course.dict())
        
        logger.info(f"✅ План контента урока {lesson_index} модуля {module_number} регенерирован")
        
        return {
            "status": "regenerated",
            "module_number": module_number,
            "lesson_index": lesson_index,
            "new_content_outline": new_content_outline
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка регенерации плана контента урока: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{course_id}/modules/{module_number}/lessons/{lesson_index}/generate", response_model=dict)
async def generate_lesson_content(course_id: int, module_number: int, lesson_index: int):
    """Сгенерировать детальный контент (лекцию со слайдами) для отдельного урока"""
    try:
        course_data = db.get_course(course_id)
        if not course_data:
            raise HTTPException(status_code=404, detail="Курс не найден")
        
        course_data.pop('id', None)
        course_data.pop('created_at', None)
        course_data.pop('updated_at', None)
        course = Course(**course_data)
        
        module = None
        for m in course.modules:
            if m.module_number == module_number:
                module = m
                break
        
        if not module or lesson_index >= len(module.lessons):
            raise HTTPException(status_code=404, detail="Модуль или урок не найден")
        
        lesson = module.lessons[lesson_index]
        
        logger.info(f"Генерация контента для урока {lesson_index} модуля {module_number} курса {course_id}")
        
        lesson_content = content_generator.generate_lesson_detailed_content(
            lesson=lesson,
            module=module,
            course_title=course.course_title,
            target_audience=course.target_audience
        )
        
        if not lesson_content:
            raise HTTPException(
                status_code=500,
                detail="Не удалось сгенерировать контент урока"
            )
        
        db.save_lesson_content(
            course_id=course_id,
            module_number=module_number,
            lesson_index=lesson_index,
            lesson_title=lesson.lesson_title,
            content_data=lesson_content
        )
        
        logger.info(f"✅ Контент урока {lesson_index} модуля {module_number} сгенерирован")
        
        return {
            "status": "generated",
            "message": f"Контент урока '{lesson.lesson_title}' сгенерирован",
            "lesson_content": lesson_content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка генерации контента урока: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{course_id}/modules/{module_number}/lessons/{lesson_index}/content", response_model=dict)
async def get_lesson_content(course_id: int, module_number: int, lesson_index: int):
    """Получить детальный контент урока"""
    try:
        content_data = db.get_lesson_content(course_id, module_number, lesson_index)
        
        if not content_data:
            raise HTTPException(
                status_code=404,
                detail="Контент урока не найден. Сначала сгенерируйте его."
            )
        
        return {
            "status": "found",
            "lesson_content": content_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения контента урока: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{course_id}/modules/{module_number}/lessons/{lesson_index}/export/{format}")
async def export_lesson_content(course_id: int, module_number: int, lesson_index: int, format: str):
    """Экспортировать детальный контент урока"""
    try:
        course_data = db.get_course(course_id)
        if not course_data:
            raise HTTPException(status_code=404, detail="Курс не найден")
        
        course_data.pop('id', None)
        course_data.pop('created_at', None)
        course_data.pop('updated_at', None)
        course = Course(**course_data)
        
        module = None
        for m in course.modules:
            if m.module_number == module_number:
                module = m
                break
        
        if not module or lesson_index >= len(module.lessons):
            raise HTTPException(status_code=404, detail="Модуль или урок не найден")
        
        lesson = module.lessons[lesson_index]
        
        content_data = db.get_lesson_content(course_id, module_number, lesson_index)
        if not content_data:
            raise HTTPException(
                status_code=404,
                detail="Детальный контент урока не найден. Сначала сгенерируйте его."
            )
        
        # Генерируем экспорт
        if format == "json":
            content = json.dumps({
                "course_title": course.course_title,
                "module_title": module.module_title,
                "lesson_title": lesson.lesson_title,
                "lesson_content": content_data
            }, ensure_ascii=False, indent=2)
            media_type = "application/json"
            extension = "json"
            
        elif format == "markdown" or format == "md":
            content = export_service.export_lesson_markdown(course, module, lesson, content_data)
            media_type = "text/markdown"
            extension = "md"
            
        elif format == "html":
            content = export_service.export_lesson_html(course, module, lesson, content_data)
            media_type = "text/html"
            extension = "html"
            
        elif format == "pptx":
            pptx_bytes = export_service.export_lesson_pptx(course, module, lesson, content_data)
            filename = safe_filename(f"Lesson_{lesson.lesson_title}", "pptx")
            
            return Response(
                content=pptx_bytes,
                media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                headers={"Content-Disposition": format_content_disposition(filename)}
            )
            
        else:
            raise HTTPException(
                status_code=400,
                detail="Неподдерживаемый формат. Используйте: json, markdown, html, pptx"
            )
        
        filename = safe_filename(f"Lesson_{lesson.lesson_title}", extension)
        
        return Response(
            content=content.encode('utf-8'),
            media_type=f"{media_type}; charset=utf-8",
            headers={"Content-Disposition": format_content_disposition(filename)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка экспорта контента урока: {e}")
        raise HTTPException(status_code=500, detail=str(e))

