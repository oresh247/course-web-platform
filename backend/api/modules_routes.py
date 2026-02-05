"""
Маршруты FastAPI для работы с модулями курса: дублирование, удаление,
генерация и экспорт детального контента.

Используемые библиотеки и концепции:
- `fastapi` — `APIRouter` для группировки endpoint-ов; `HTTPException` для ошибок.
- `pydantic.BaseModel` — описание тел запросов с валидацией (например, DuplicateModuleRequest).
- `logging` — логируем шаги и ошибки для последующей диагностики.
"""
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
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
class DuplicateModuleRequest(BaseModel):
    """Тело запроса для дублирования модуля.

    Поля перезаписывают заголовок и цель будущего модуля-копии.
    """
    module_title: str
    module_goal: str


@router.post("/{course_id}/modules/{module_number}/duplicate", response_model=dict)
async def duplicate_module(course_id: int, module_number: int, body: DuplicateModuleRequest):
    """Создать полную копию модуля (включая детальный контент) с новым номером."""
    try:
        course_data = db.get_course(course_id)
        if not course_data:
            raise HTTPException(status_code=404, detail="Курс не найден")

        # Восстанавливаем модель курса
        course_data.pop('id', None)
        course_data.pop('created_at', None)
        course_data.pop('updated_at', None)
        course = Course(**course_data)

        # Ищем исходный модуль
        source_module = None
        for m in course.modules:
            if m.module_number == module_number:
                source_module = m
                break
        if not source_module:
            raise HTTPException(status_code=404, detail="Модуль не найден")

        # Новый номер модуля = max + 1
        new_number = max((m.module_number for m in course.modules), default=0) + 1

        # Глубокая копия структуры модуля
        import copy
        new_module = copy.deepcopy(source_module)
        new_module.module_number = new_number
        new_module.module_title = body.module_title
        new_module.module_goal = body.module_goal

        # Добавляем модуль в курс и сохраняем курс
        course.modules.append(new_module)
        saved = db.update_course(course_id, course.dict())
        if not saved:
            raise HTTPException(status_code=500, detail="Не удалось сохранить копию модуля в курсе")

        # Копируем детальный контент модуля, если есть
        try:
            src_module_content = db.get_module_content(course_id, module_number)
            if src_module_content:
                db.save_module_content(
                    course_id=course_id,
                    module_number=new_number,
                    module_title=new_module.module_title,
                    content_data=src_module_content
                )
        except Exception as e:
            logger.warning(f"Не удалось скопировать детальный контент модуля: {e}")

        # Копируем детальный контент уроков
        try:
            for idx, lesson in enumerate(new_module.lessons):
                src_lesson_content = db.get_lesson_content(course_id, module_number, idx)
                if src_lesson_content:
                    db.save_lesson_content(
                        course_id=course_id,
                        module_number=new_number,
                        lesson_index=idx,
                        lesson_title=lesson.lesson_title,
                        content_data=src_lesson_content
                    )
        except Exception as e:
            logger.warning(f"Не удалось скопировать контент уроков: {e}")

        return {
            "status": "duplicated",
            "new_module_number": new_number,
            "module_title": new_module.module_title
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка дублирования модуля: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{course_id}/modules/{module_number}", response_model=dict)
async def delete_module(course_id: int, module_number: int):
    """Удалить модуль из курса и все связанный детальный контент (модуль+уроки)."""
    try:
        course_data = db.get_course(course_id)
        if not course_data:
            raise HTTPException(status_code=404, detail="Курс не найден")
        # Работаем с «сырыми» данными курса без строгой валидации, чтобы избежать ошибок схем
        raw_course = dict(course_data)
        raw_course.pop('id', None)
        raw_course.pop('created_at', None)
        raw_course.pop('updated_at', None)
        modules = raw_course.get('modules') or []
        before_count = len(modules)
        # Сравниваем как числа
        filtered_modules = [m for m in modules if int(m.get('module_number', -1)) != int(module_number)]
        if len(filtered_modules) == before_count:
            raise HTTPException(status_code=404, detail="Модуль не найден")
        raw_course['modules'] = filtered_modules

        saved = db.update_course(course_id, raw_course)
        if not saved:
            raise HTTPException(status_code=500, detail="Не удалось обновить курс")

        # Удаляем детальный контент модуля и уроков
        del_mod = db.delete_module_content(course_id, module_number)
        del_lessons = db.delete_lesson_contents_for_module(course_id, module_number)
        logger.info(f"Удалён модуль {module_number}: module_contents={del_mod}, lesson_contents={del_lessons}")

        return {"status": "deleted", "module_number": module_number}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления модуля: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
        
        module_content = await run_in_threadpool(
            content_generator.generate_module_content,
            module=module,
            course_title=course.course_title,
            target_audience=course.target_audience,
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

