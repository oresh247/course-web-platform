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
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
import json

from backend.models.domain import Course, Module
from backend.ai.content_generator import ContentGenerator
from backend.database import db
from backend.services.generation_service import generation_service
from backend.services.test_generator_service import TestGeneratorService
from backend.services.export_service import export_service
from backend.utils.formatters import safe_filename, format_content_disposition
from fastapi.responses import Response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/courses", tags=["modules"])

# Инициализируем генератор контента
content_generator = ContentGenerator()
test_generator = TestGeneratorService()
class DuplicateModuleRequest(BaseModel):
    """Тело запроса для дублирования модуля.

    Поля перезаписывают заголовок и цель будущего модуля-копии.
    """
    module_title: str
    module_goal: str


class GenerateModuleTestsRequest(BaseModel):
    """Запрос на генерацию тестов для всех уроков модуля."""

    num_questions: int = Field(default=10, ge=5, le=20, description="Количество вопросов в тесте")
    model: Optional[str] = Field(default=None, description="Модель AI")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="Температура")
    max_tokens: Optional[int] = Field(default=None, ge=100, description="Макс. токенов")


def build_module_content_from_lessons(
    course_id: int,
    module: Module,
) -> Dict[str, Any]:
    lectures: List[Dict[str, Any]] = []
    total_slides = 0
    total_duration = 0

    for lesson_index, lesson in enumerate(module.lessons):
        lesson_content = db.get_lesson_content(course_id, module.module_number, lesson_index)
        if not lesson_content:
            continue

        slides = lesson_content.get("slides", [])
        if not isinstance(slides, list):
            slides = []

        duration_minutes = lesson_content.get("duration_minutes", lesson.estimated_time_minutes)
        if not isinstance(duration_minutes, (int, float)):
            duration_minutes = lesson.estimated_time_minutes

        lecture = {
            "lecture_title": lesson_content.get("lecture_title", lesson.lesson_title),
            "module_number": module.module_number,
            "module_title": module.module_title,
            "duration_minutes": int(duration_minutes) if duration_minutes else 0,
            "learning_objectives": lesson_content.get("learning_objectives", []),
            "key_takeaways": lesson_content.get("key_takeaways", []),
            "slides": slides,
        }
        lectures.append(lecture)
        total_slides += len(slides)
        total_duration += lecture["duration_minutes"]

    return {
        "module_number": module.module_number,
        "module_title": module.module_title,
        "lectures": lectures,
        "total_slides": total_slides,
        "estimated_duration_minutes": total_duration,
    }


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
    """Сгенерировать детальный контент для всех уроков модуля"""
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
        
        logger.info(f"Генерация контента уроков для модуля {module_number} курса {course_id}")

        generated_lessons = []
        skipped_lessons = []
        failed_lessons = []

        for lesson_index, lesson in enumerate(module.lessons):
            existing_content = db.get_lesson_content(course_id, module.module_number, lesson_index)
            if existing_content:
                skipped_lessons.append(lesson_index)
                continue

            logger.info(
                f"Генерация детального контента для урока {lesson_index} "
                f"модуля {module_number} курса {course_id}"
            )
            lesson_content = await run_in_threadpool(
                content_generator.generate_lesson_detailed_content,
                lesson=lesson,
                module=module,
                course_title=course.course_title,
                target_audience=course.target_audience,
            )

            if not lesson_content:
                failed_lessons.append(lesson_index)
                continue

            db.save_lesson_content(
                course_id=course_id,
                module_number=module_number,
                lesson_index=lesson_index,
                lesson_title=lesson.lesson_title,
                content_data=lesson_content,
            )
            generated_lessons.append(lesson_index)

        module_content = build_module_content_from_lessons(course_id, module)
        if not module_content.get("lectures"):
            raise HTTPException(
                status_code=500,
                detail="Не удалось сгенерировать контент модуля"
            )

        db.save_module_content(
            course_id=course_id,
            module_number=module_number,
            module_title=module.module_title,
            content_data=module_content,
        )

        logger.info(f"✅ Контент модуля {module_number} обновлен и сохранен")

        return {
            "status": "generated" if not failed_lessons else "partial",
            "message": f"Контент модуля '{module.module_title}' сгенерирован",
            "module_content": module_content,
            "generated_lessons": generated_lessons,
            "skipped_lessons": skipped_lessons,
            "failed_lessons": failed_lessons,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка генерации контента модуля: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{course_id}/modules/{module_number}/generate-tests", response_model=dict)
async def generate_module_tests(
    course_id: int,
    module_number: int,
    body: GenerateModuleTestsRequest = GenerateModuleTestsRequest(),
):
    """Сгенерировать тесты для всех уроков модуля, где их еще нет."""
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

        logger.info(f"Генерация тестов для модуля {module_number} курса {course_id}")

        generated_lessons = []
        skipped_lessons = []
        failed_lessons = []

        for lesson_index, lesson in enumerate(module.lessons):
            existing_test = db.get_lesson_test(course_id, module_number, lesson_index)
            if existing_test:
                skipped_lessons.append(lesson_index)
                continue

            test = await run_in_threadpool(
                test_generator.generate_test,
                lesson_title=lesson.lesson_title,
                lesson_goal=lesson.lesson_goal,
                content_outline=lesson.content_outline,
                course_title=course.course_title,
                target_audience=course.target_audience,
                module_title=module.module_title,
                num_questions=body.num_questions,
                model=body.model,
                temperature=body.temperature,
                max_tokens=body.max_tokens,
            )

            if not test:
                failed_lessons.append(lesson_index)
                continue

            db.save_lesson_test(
                course_id=course_id,
                module_number=module_number,
                lesson_index=lesson_index,
                lesson_title=lesson.lesson_title,
                test_data=test.dict(),
            )
            generated_lessons.append(lesson_index)

        return {
            "status": "generated" if not failed_lessons else "partial",
            "message": f"Тесты для модуля '{module.module_title}' сгенерированы",
            "generated_lessons": generated_lessons,
            "skipped_lessons": skipped_lessons,
            "failed_lessons": failed_lessons,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка генерации тестов модуля: {e}")
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

