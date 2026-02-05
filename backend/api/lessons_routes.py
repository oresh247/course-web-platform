"""
Маршруты FastAPI для работы с уроками: дублирование/удаление уроков,
AI‑регенерация контента и экспорт.

Используемые библиотеки и концепции:
- `fastapi` — `APIRouter`, `HTTPException`, `Response`.
- `pydantic.BaseModel` — описание и валидация входных тел запросов.
- `logging` — логируем ключевые шаги и ошибки.
"""
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from typing import Optional
import logging
import json

from backend.models.domain import Course, LessonTest
from backend.ai.content_generator import ContentGenerator
from backend.database import db
from backend.services.generation_service import generation_service
from backend.services.test_generator_service import TestGeneratorService
from backend.services.export_service import export_service
from backend.utils.formatters import safe_filename, format_content_disposition
from fastapi.responses import Response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/courses", tags=["lessons"])

# Инициализируем генератор контента
content_generator = ContentGenerator()
test_generator = TestGeneratorService()
class DuplicateLessonRequest(BaseModel):
    """Тело запроса для дублирования урока.

    Позволяет задать новое имя, цель и (опционально) план контента/оценку
    до фактического копирования.
    """
    lesson_title: str
    lesson_goal: str
    content_outline: list[str] | None = None
    assessment: str | None = None


@router.post("/{course_id}/modules/{module_number}/lessons/{lesson_index}/duplicate", response_model=dict)
async def duplicate_lesson(course_id: int, module_number: int, lesson_index: int, body: DuplicateLessonRequest):
    """Создать полную копию урока (включая детальный контент) с новым индексом."""
    try:
        course_data = db.get_course(course_id)
        if not course_data:
            raise HTTPException(status_code=404, detail="Курс не найден")

        # Работаем с сырыми данными
        raw_course = dict(course_data)
        raw_course.pop('id', None)
        raw_course.pop('created_at', None)
        raw_course.pop('updated_at', None)

        modules = raw_course.get('modules') or []
        source_module = next((m for m in modules if int(m.get('module_number', -1)) == int(module_number)), None)
        if not source_module:
            raise HTTPException(status_code=404, detail="Модуль не найден")
        lessons = source_module.get('lessons') or []
        if lesson_index < 0 or lesson_index >= len(lessons):
            raise HTTPException(status_code=404, detail="Урок не найден")

        import copy
        new_lesson = copy.deepcopy(lessons[lesson_index])
        new_lesson['lesson_title'] = body.lesson_title
        new_lesson['lesson_goal'] = body.lesson_goal
        if body.content_outline is not None:
            new_lesson['content_outline'] = body.content_outline
        if body.assessment is not None:
            new_lesson['assessment'] = body.assessment

        lessons.append(new_lesson)
        source_module['lessons'] = lessons
        raw_course['modules'] = modules

        saved = db.update_course(course_id, raw_course)
        if not saved:
            raise HTTPException(status_code=500, detail="Не удалось сохранить копию урока")

        # Новый индекс — в конце списка
        new_index = len(lessons) - 1

        # Копируем детальный контент урока, если есть
        try:
            src_content = db.get_lesson_content(course_id, module_number, lesson_index)
            if src_content:
                db.save_lesson_content(
                    course_id=course_id,
                    module_number=module_number,
                    lesson_index=new_index,
                    lesson_title=new_lesson.get('lesson_title') or '',
                    content_data=src_content
                )
        except Exception as e:
            logger.warning(f"Не удалось скопировать контент урока: {e}")

        return {"status": "duplicated", "new_lesson_index": new_index}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка дублирования урока: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{course_id}/modules/{module_number}/lessons/{lesson_index}", response_model=dict)
async def delete_lesson(course_id: int, module_number: int, lesson_index: int):
    """Удалить урок из модуля и его детальный контент."""
    try:
        course_data = db.get_course(course_id)
        if not course_data:
            raise HTTPException(status_code=404, detail="Курс не найден")

        raw_course = dict(course_data)
        raw_course.pop('id', None)
        raw_course.pop('created_at', None)
        raw_course.pop('updated_at', None)

        modules = raw_course.get('modules') or []
        source_module = next((m for m in modules if int(m.get('module_number', -1)) == int(module_number)), None)
        if not source_module:
            raise HTTPException(status_code=404, detail="Модуль не найден")
        lessons = source_module.get('lessons') or []
        if lesson_index < 0 or lesson_index >= len(lessons):
            raise HTTPException(status_code=404, detail="Урок не найден")

        # Удаляем урок
        del lessons[lesson_index]
        source_module['lessons'] = lessons
        raw_course['modules'] = modules

        saved = db.update_course(course_id, raw_course)
        if not saved:
            raise HTTPException(status_code=500, detail="Не удалось обновить курс")

        # Удаляем детальный контент урока
        try:
            _ = db.delete_lesson_content(course_id, module_number, lesson_index)
        except Exception as e:
            logger.warning(f"Не удалось удалить контент урока: {e}")

        return {"status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка удаления урока: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class RegenerateLessonContentRequest(BaseModel):
    """Тело запроса для регенерации плана контента урока"""
    lesson_title: str | None = None
    lesson_goal: str | None = None

@router.post("/{course_id}/modules/{module_number}/lessons/{lesson_index}/regenerate-content", response_model=dict)
async def regenerate_lesson_content(
    course_id: int, 
    module_number: int, 
    lesson_index: int,
    body: RegenerateLessonContentRequest | None = None
):
    """Регенерировать план контента урока с помощью AI
    
    Args:
        course_id: ID курса
        module_number: Номер модуля
        lesson_index: Индекс урока
        body: Опциональные параметры (lesson_title, lesson_goal) для использования актуальных значений из формы
    """
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
        
        # Используем значения из запроса, если они переданы, иначе берем из базы данных
        lesson_title = body.lesson_title if body and body.lesson_title else lesson.lesson_title
        lesson_goal = body.lesson_goal if body and body.lesson_goal else lesson.lesson_goal
        
        # Если переданы новые значения, сначала обновляем урок в базе данных
        if body and (body.lesson_title or body.lesson_goal):
            lesson.lesson_title = lesson_title
            lesson.lesson_goal = lesson_goal
            db.update_course(course_id, course.dict())
        
        new_content_outline = generation_service.regenerate_lesson_content_outline(
            course_title=course.course_title,
            module_title=module.module_title,
            lesson_title=lesson_title,
            lesson_goal=lesson_goal,
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
        
        lesson_content = await run_in_threadpool(
            content_generator.generate_lesson_detailed_content,
            lesson=lesson,
            module=module,
            course_title=course.course_title,
            target_audience=course.target_audience,
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


# ============================================================================
# API ENDPOINTS ДЛЯ РАБОТЫ С ТЕСТАМИ
# ============================================================================

class GenerateTestRequest(BaseModel):
    """Запрос на генерацию теста с настройками AI"""
    num_questions: int = Field(default=10, ge=5, le=20, description="Количество вопросов")
    model: Optional[str] = Field(default=None, description="Модель AI (если не указана, используется настройка по умолчанию)")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=2.0, description="Температура для генерации")
    max_tokens: Optional[int] = Field(default=None, ge=100, description="Максимальное количество токенов")


class UpdateTestRequest(BaseModel):
    """Запрос на обновление теста"""
    test: LessonTest


@router.post("/{course_id}/modules/{module_number}/lessons/{lesson_index}/generate-test", response_model=dict)
async def generate_lesson_test(
    course_id: int,
    module_number: int,
    lesson_index: int,
    body: GenerateTestRequest = GenerateTestRequest()
):
    """Сгенерировать тест для урока с использованием AI"""
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
        
        logger.info(f"Генерация теста для урока {lesson_index} модуля {module_number} курса {course_id}")
        
        # Генерируем тест
        test = test_generator.generate_test(
            lesson_title=lesson.lesson_title,
            lesson_goal=lesson.lesson_goal,
            content_outline=lesson.content_outline,
            course_title=course.course_title,
            target_audience=course.target_audience,
            module_title=module.module_title,
            num_questions=body.num_questions,
            model=body.model,
            temperature=body.temperature,
            max_tokens=body.max_tokens
        )
        
        if not test:
            raise HTTPException(
                status_code=500,
                detail="Не удалось сгенерировать тест"
            )
        
        # Сохраняем тест в БД
        db.save_lesson_test(
            course_id=course_id,
            module_number=module_number,
            lesson_index=lesson_index,
            lesson_title=lesson.lesson_title,
            test_data=test.dict()
        )
        
        logger.info(f"✅ Тест для урока {lesson_index} модуля {module_number} сгенерирован")
        
        return {
            "status": "generated",
            "message": f"Тест для урока '{lesson.lesson_title}' сгенерирован",
            "test": test.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка генерации теста: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{course_id}/modules/{module_number}/lessons/{lesson_index}/test", response_model=dict)
async def get_lesson_test(course_id: int, module_number: int, lesson_index: int):
    """Получить тест для урока"""
    try:
        test_data = db.get_lesson_test(course_id, module_number, lesson_index)
        
        if not test_data:
            raise HTTPException(
                status_code=404,
                detail="Тест не найден. Сначала сгенерируйте его."
            )
        
        return {
            "status": "found",
            "test": test_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка получения теста: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{course_id}/modules/{module_number}/lessons/{lesson_index}/test", response_model=dict)
async def update_lesson_test(
    course_id: int,
    module_number: int,
    lesson_index: int,
    body: UpdateTestRequest
):
    """Обновить тест для урока"""
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
        
        # Валидация теста через Pydantic
        try:
            test = LessonTest(**body.test.dict())
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Невалидные данные теста: {e}")
        
        # Сохраняем обновленный тест
        db.save_lesson_test(
            course_id=course_id,
            module_number=module_number,
            lesson_index=lesson_index,
            lesson_title=lesson.lesson_title,
            test_data=test.dict()
        )
        
        logger.info(f"✅ Тест для урока {lesson_index} модуля {module_number} обновлен")
        
        return {
            "status": "updated",
            "message": f"Тест для урока '{lesson.lesson_title}' обновлен",
            "test": test.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка обновления теста: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{course_id}/modules/{module_number}/lessons/{lesson_index}/regenerate-test", response_model=dict)
async def regenerate_lesson_test(
    course_id: int,
    module_number: int,
    lesson_index: int,
    body: GenerateTestRequest = GenerateTestRequest()
):
    """Перегенерировать тест для урока (аналогично generate, но обновляет существующий)"""
    # Используем тот же endpoint, что и generate, но с другим названием для ясности
    return await generate_lesson_test(course_id, module_number, lesson_index, body)

