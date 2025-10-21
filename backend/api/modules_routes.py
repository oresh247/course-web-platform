"""
API endpoints для работы с модулями курса
"""
from fastapi import APIRouter, HTTPException
import logging
import json

from backend.models.domain import Course, Module
from backend.ai.content_generator import ContentGenerator
from backend.database import db
from backend.services.generation_service import generation_service
from backend.services.export_service import export_service
from backend.utils.formatters import safe_filename, format_content_disposition
from fastapi.responses import Response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/courses", tags=["modules"])

# Инициализируем генератор контента
content_generator = ContentGenerator()


@router.post("/{course_id}/modules/{module_number}/generate", response_model=dict)
async def generate_module_content(course_id: int, module_number: int):
    """Сгенерировать контент (лекции и слайды) для модуля"""
    try:
        course_data = db.get_course(course_id)
        if not course_data:
            raise HTTPException(status_code=404, detail="Курс не найден")
        
        course_data.pop('id', None)
        course_data.pop('created_at', None)
        course_data.pop('updated_at', None)
        
        course = Course(**course_data)
        
        # Находим модуль
        module = None
        for m in course.modules:
            if m.module_number == module_number:
                module = m
                break
        
        if not module:
            raise HTTPException(status_code=404, detail="Модуль не найден")
        
        logger.info(f"Генерация контента для модуля {module_number} курса {course_id}")
        
        module_content = content_generator.generate_module_content(
            module=module,
            course_title=course.course_title,
            target_audience=course.target_audience
        )
        
        if not module_content:
            raise HTTPException(
                status_code=500,
                detail="Не удалось сгенерировать контент модуля"
            )
        
        db.save_module_content(
            course_id=course_id,
            module_number=module_number,
            module_title=module.module_title,
            content_data=module_content.dict()
        )
        
        logger.info(f"✅ Контент модуля {module_number} сгенерирован и сохранен")
        
        return {
            "status": "generated",
            "message": f"Контент модуля '{module.module_title}' сгенерирован",
            "module_content": module_content.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка генерации контента модуля: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{course_id}/modules/{module_number}/regenerate-goal", response_model=dict)
async def regenerate_module_goal(course_id: int, module_number: int):
    """Регенерировать цель модуля с помощью AI"""
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
        
        if not module:
            raise HTTPException(status_code=404, detail="Модуль не найден")
        
        new_goal = generation_service.regenerate_module_goal(
            course_title=course.course_title,
            target_audience=course.target_audience,
            module_number=module.module_number,
            module_title=module.module_title
        )
        
        if not new_goal:
            raise HTTPException(status_code=500, detail="Не удалось регенерировать цель")
        
        module.module_goal = new_goal
        db.update_course(course_id, course.dict())
        
        logger.info(f"✅ Цель модуля {module_number} регенерирована")
        
        return {
            "status": "regenerated",
            "module_number": module_number,
            "new_goal": new_goal
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка регенерации цели модуля: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{course_id}/modules/{module_number}/content", response_model=dict)
async def get_module_content(course_id: int, module_number: int):
    """Получить контент модуля (лекции и слайды)"""
    try:
        content_data = db.get_module_content(course_id, module_number)
        
        if not content_data:
            raise HTTPException(
                status_code=404,
                detail="Контент модуля не найден. Сначала сгенерируйте его."
            )
        
        return {
            "status": "found",
            "module_content": content_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения контента модуля: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{course_id}/modules/{module_number}/export/{format}")
async def export_module_content(course_id: int, module_number: int, format: str):
    """Экспортировать детальный контент модуля"""
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
        
        if not module:
            raise HTTPException(status_code=404, detail="Модуль не найден")
        
        content_data = db.get_module_content(course_id, module_number)
        if not content_data:
            raise HTTPException(
                status_code=404,
                detail="Детальный контент модуля не найден. Сначала сгенерируйте его."
            )
        
        # Генерируем экспорт
        if format == "json":
            content = json.dumps({
                "course_title": course.course_title,
                "module_title": module.module_title,
                "module_content": content_data
            }, ensure_ascii=False, indent=2)
            media_type = "application/json"
            extension = "json"
            
        elif format == "markdown" or format == "md":
            content = export_service.export_module_markdown(course, module, content_data)
            media_type = "text/markdown"
            extension = "md"
            
        elif format == "html":
            content = export_service.export_module_html(course, module, content_data)
            media_type = "text/html"
            extension = "html"
            
        elif format == "pptx":
            pptx_bytes = export_service.export_module_pptx(course, module, content_data)
            filename = safe_filename(f"Module_{module_number}_{module.module_title}", "pptx")
            
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
        
        filename = safe_filename(f"Module_{module_number}_{module.module_title}", extension)
        
        return Response(
            content=content.encode('utf-8'),
            media_type=f"{media_type}; charset=utf-8",
            headers={"Content-Disposition": format_content_disposition(filename)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка экспорта контента модуля: {e}")
        raise HTTPException(status_code=500, detail=str(e))

