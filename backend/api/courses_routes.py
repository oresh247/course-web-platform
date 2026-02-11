"""
Маршруты FastAPI для создания и управления курсами (CRUD + экспорт).

Используемые библиотеки и концепции:
- `fastapi` — веб‑фреймворк. `APIRouter` группирует маршруты, `HTTPException`
  возвращает ошибки с нужным статус‑кодом. `Response` — для отдачи файлов.
- `pydantic` модели из `backend.models.domain` — строгая валидация входных/выходных данных.
- `logging` — логирование действий и ошибок для диагностики.
"""
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from typing import List
import logging
import json

from backend.models.domain import (
    Course, CourseCreateRequest, CourseResponse
)
from backend.ai.openai_client import OpenAIClient
from backend.database import db
from backend.services.export_service import export_service
from backend.services.export.scorm import SCORM_VERSION_12, SCORM_VERSION_2004
from backend.utils.formatters import safe_filename, format_content_disposition
from fastapi.responses import Response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/courses", tags=["courses"])

# Инициализируем AI клиент
openai_client = OpenAIClient()


@router.post("/", response_model=CourseResponse)
async def create_course(request: CourseCreateRequest):
    """Создать новую структуру курса с помощью AI"""
    try:
        logger.info(f"Создание курса: {request.topic}")
        
        course_data = await run_in_threadpool(
            openai_client.generate_course_structure,
            topic=request.topic,
            audience_level=request.audience_level.value,
            module_count=request.module_count,
            course_goals=request.course_goals,
            duration_weeks=request.duration_weeks,
            hours_per_week=request.hours_per_week,
        )
        
        if not course_data:
            raise HTTPException(
                status_code=500,
                detail="Не удалось сгенерировать структуру курса. Проверьте настройки OpenAI API."
            )
        
        # Гарантируем, что длительность видна на карточке курсов
        # hours_per_week маппим в duration_hours (для отображения "N недель (X часов)")
        if request.hours_per_week is not None:
            try:
                course_data["duration_hours"] = int(request.hours_per_week)
            except Exception:
                course_data["duration_hours"] = request.hours_per_week
        if request.duration_weeks is not None:
            course_data["duration_weeks"] = request.duration_weeks

        if request.course_goals:
            course_data["course_goals"] = request.course_goals

        course = Course(**course_data)
        course_id = db.save_course(course.dict())
        
        logger.info(f"✅ Курс создан с ID: {course_id}")
        
        # Добавляем course_id в данные курса
        course_dict = course.dict()
        course_dict["course_id"] = course_id
        
        return {
            "id": course_id,
            "course_id": course_id,
            "course": course_dict,
            "status": "created",
            "message": f"Курс '{course.course_title}' успешно создан"
        }
        
    except ValueError as e:
        logger.error(f"Ошибка валидации: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка создания курса: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[dict])
async def get_courses(limit: int = 50, offset: int = 0):
    """Получить список всех курсов"""
    try:
        courses = db.get_all_courses(limit=limit, offset=offset)
        return courses
    except Exception as e:
        logger.error(f"Ошибка получения списка курсов: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{course_id}", response_model=CourseResponse)
async def get_course(course_id: int):
    """Получить курс по ID"""
    try:
        course_data = db.get_course(course_id)
        
        if not course_data:
            raise HTTPException(status_code=404, detail="Курс не найден")
        
        saved_id = course_data.pop('id', None)
        course_data.pop('created_at', None)
        course_data.pop('updated_at', None)
        
        course = Course(**course_data)
        
        return CourseResponse(
            id=saved_id,
            course=course,
            status="found",
            message=f"Курс '{course.course_title}' загружен"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения курса {course_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{course_id}", response_model=CourseResponse)
async def update_course(course_id: int, course: Course):
    """Обновить курс"""
    try:
        existing = db.get_course(course_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Курс не найден")
        
        success = db.update_course(course_id, course.dict())
        
        if not success:
            raise HTTPException(status_code=500, detail="Не удалось обновить курс")
        
        logger.info(f"✅ Курс {course_id} обновлен")
        
        return CourseResponse(
            id=course_id,
            course=course,
            status="updated",
            message=f"Курс '{course.course_title}' обновлен"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления курса {course_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{course_id}")
async def delete_course(course_id: int):
    """Удалить курс"""
    try:
        success = db.delete_course(course_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Курс не найден")
        
        logger.info(f"✅ Курс {course_id} удален")
        
        return {"status": "deleted", "message": f"Курс удален"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления курса {course_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{course_id}/export/{format}")
async def export_course(course_id: int, format: str, include_videos: bool = False):
    """Экспортировать курс в указанном формате
    
    Args:
        course_id: ID курса
        format: Формат экспорта (json, markdown, txt, html, pptx, scorm, scorm2004, scorm_single)
        include_videos: Включать ли видео в SCORM пакет (только для форматов scorm/scorm2004)
    """
    try:
        course_data = db.get_course(course_id)
        if not course_data:
            raise HTTPException(status_code=404, detail="Курс не найден")
        
        course_data.pop('id', None)
        course_data.pop('created_at', None)
        course_data.pop('updated_at', None)
        
        course = Course(**course_data)
        
        # Генерируем контент
        if format == "json":
            content = json.dumps(course.dict(), ensure_ascii=False, indent=2)
            media_type = "application/json"
            extension = "json"
            
        elif format == "markdown" or format == "md":
            content = export_service.export_course_markdown(course, course_id=course_id)
            media_type = "text/markdown"
            extension = "md"
            
        elif format == "txt":
            content = export_service.export_course_text(course)
            media_type = "text/plain"
            extension = "txt"
            
        elif format == "html":
            content = export_service.export_course_html(course)
            media_type = "text/html"
            extension = "html"
            
        elif format == "pptx":
            pptx_bytes = export_service.export_course_pptx(course)
            filename = safe_filename(course.course_title, "pptx")
            
            return Response(
                content=pptx_bytes,
                media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                headers={"Content-Disposition": format_content_disposition(filename)}
            )
            
        elif format in {"scorm", "zip", "scorm12", "scorm-12", "scorm_12"}:
            scorm_bytes = export_service.export_course_scorm(
                course,
                course_id,
                include_videos=include_videos,
                scorm_version=SCORM_VERSION_12,
            )
            filename = safe_filename(course.course_title, "zip")
            
            return Response(
                content=scorm_bytes,
                media_type="application/zip",
                headers={"Content-Disposition": format_content_disposition(filename)}
            )
            
        elif format in {"scorm2004", "scorm-2004", "scorm_2004"}:
            scorm_bytes = export_service.export_course_scorm(
                course,
                course_id,
                include_videos=include_videos,
                scorm_version=SCORM_VERSION_2004,
            )
            filename = safe_filename(course.course_title, "zip")
            
            return Response(
                content=scorm_bytes,
                media_type="application/zip",
                headers={"Content-Disposition": format_content_disposition(filename)}
            )

        elif format in {"scorm_single", "scorm12_single", "scorm-single"}:
            scorm_bytes = export_service.export_course_scorm(
                course,
                course_id,
                include_videos=include_videos,
                scorm_version=SCORM_VERSION_12,
                single_sco=True,
            )
            filename = safe_filename(course.course_title, "zip")

            return Response(
                content=scorm_bytes,
                media_type="application/zip",
                headers={"Content-Disposition": format_content_disposition(filename)}
            )

        else:
            raise HTTPException(
                status_code=400,
                detail="Неподдерживаемый формат. Используйте: json, markdown, txt, html, pptx, scorm, scorm2004, scorm_single"
            )
        
        # Формируем имя файла
        filename = safe_filename(course.course_title, extension)
        
        return Response(
            content=content.encode('utf-8'),
            media_type=f"{media_type}; charset=utf-8",
            headers={"Content-Disposition": format_content_disposition(filename)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка экспорта курса: {e}")
        raise HTTPException(status_code=500, detail=str(e))

