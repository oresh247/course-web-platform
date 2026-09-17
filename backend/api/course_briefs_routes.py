"""HTTP-маршруты интервью по уточнению структуры курса."""
import logging

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from backend.models.domain import (
    CourseBriefAnswerRequest,
    CourseBriefPublishResponse,
    CourseBriefResponse,
    CourseBriefStartRequest,
)
from backend.services.course_brief_service import (
    CourseBriefGenerationError,
    CourseBriefInvalidStateError,
    CourseBriefNotFoundError,
    course_brief_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/course-briefs", tags=["course-briefs"])


@router.post("/", response_model=CourseBriefResponse, status_code=201)
async def start_course_brief(request: CourseBriefStartRequest):
    """Запускает интервью и возвращает первый вопрос без черновой структуры."""
    try:
        return await run_in_threadpool(
            course_brief_service.start,
            request.topic,
            course_goals=request.course_goals,
            audience_level=(
                request.audience_level.value if request.audience_level is not None else None
            ),
            module_count=request.module_count,
            duration_weeks=request.duration_weeks,
            hours_per_week=request.hours_per_week,
        )
    except CourseBriefGenerationError as error:
        logger.error("Не удалось запустить интервью: %s", error)
        raise HTTPException(status_code=503, detail=str(error))
    except Exception as error:
        logger.exception("Непредвиденная ошибка при запуске интервью")
        raise HTTPException(status_code=500, detail="Не удалось начать уточнение структуры курса") from error


@router.get("/{session_id}", response_model=CourseBriefResponse)
async def get_course_brief(session_id: str):
    """Возвращает сохранённое состояние интервью после перезагрузки страницы."""
    try:
        return await run_in_threadpool(course_brief_service.get_state, session_id)
    except CourseBriefNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except Exception as error:
        logger.exception("Не удалось получить состояние интервью")
        raise HTTPException(status_code=500, detail="Не удалось получить состояние уточнения") from error


@router.post("/{session_id}/answers", response_model=CourseBriefResponse)
async def answer_course_brief(session_id: str, request: CourseBriefAnswerRequest):
    """Сохраняет ответ пользователя и возвращает следующий вопрос либо финальный outline."""
    try:
        return await run_in_threadpool(course_brief_service.answer, session_id, request)
    except CourseBriefNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except CourseBriefInvalidStateError as error:
        raise HTTPException(status_code=409, detail=str(error))
    except Exception as error:
        logger.exception("Не удалось обработать ответ в интервью")
        raise HTTPException(status_code=500, detail="Не удалось обработать ответ") from error


@router.post(
    "/{session_id}/publish",
    response_model=CourseBriefPublishResponse,
    status_code=201,
)
async def publish_course_brief(session_id: str):
    """Публикует финальную структуру интервью в список курсов."""
    try:
        return await run_in_threadpool(course_brief_service.publish, session_id)
    except CourseBriefNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except CourseBriefInvalidStateError as error:
        raise HTTPException(status_code=409, detail=str(error))
    except Exception as error:
        logger.exception("Не удалось опубликовать курс из интервью")
        raise HTTPException(
            status_code=500,
            detail="Не удалось сохранить курс в список «Мои курсы»",
        ) from error