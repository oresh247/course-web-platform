"""Проверки сценария интервью без сети, БД и настоящей модели."""
from typing import Any, Dict, List

from backend.models.domain import (
    CourseBriefAnswerRequest,
    CourseBriefDepth,
    CourseBriefStatus,
    DifficultyLevel,
)
from backend.services.course_brief_service import CourseBriefService
from backend.services.course_brief_service import CourseBriefInvalidStateError


class FakeStorage:
    """Минимальное долговечное хранилище в памяти для unit-теста сервиса."""

    def __init__(self):
        self.records: Dict[str, Dict[str, Any]] = {}
        self.messages: List[Dict[str, Any]] = []

    def create_course_brief(self, record: Dict[str, Any]) -> str:
        self.records[record["id"]] = dict(record)
        return record["id"]

    def get_course_brief(self, brief_id: str):
        record = self.records.get(brief_id)
        return dict(record) if record else None

    def update_course_brief(self, brief_id: str, updates: Dict[str, Any], expected_revision=None) -> bool:
        if expected_revision is not None and self.records[brief_id]["revision"] != expected_revision:
            return False
        self.records[brief_id].update(updates)
        return True

    def add_course_brief_message(self, brief_id: str, role: str, content: str, sequence: int):
        self.messages.append(
            {
                "brief_id": brief_id,
                "role": role,
                "content": content,
                "sequence": sequence,
            }
        )

    def get_course_brief_messages(self, brief_id: str):
        return [message for message in self.messages if message["brief_id"] == brief_id]


class FakeAIClient:
    """Возвращает стабильный черновик, а финализацию отдаёт fallback-логике сервиса."""

    def generate_course_structure(self, **_kwargs):
        return {
            "course_title": "Python для аналитики",
            "course_goals": "Научиться применять Python в задачах аналитики",
            "target_audience": "middle",
            "duration_weeks": 4,
            "modules": [
                {
                    "module_number": 1,
                    "module_title": "Основы Python",
                    "module_goal": "Освоить базовый синтаксис.",
                    "lessons": [
                        {
                            "lesson_title": "Переменные и типы",
                            "lesson_goal": "Работать с основными типами.",
                            "content_outline": ["Типы", "Переменные"],
                            "assessment": "Упражнение",
                            "format": "theory",
                            "estimated_time_minutes": 45,
                        }
                    ],
                },
                {
                    "module_number": 2,
                    "module_title": "Работа с таблицами",
                    "module_goal": "Анализировать табличные данные.",
                    "lessons": [
                        {
                            "lesson_title": "Pandas",
                            "lesson_goal": "Загружать и фильтровать данные.",
                            "content_outline": ["DataFrame", "Фильтрация"],
                            "assessment": "Практика",
                            "format": "practice",
                            "estimated_time_minutes": 60,
                        }
                    ],
                },
            ],
        }

    def call_ai_json(self, **_kwargs):
        return None


class RefiningFakeAIClient(FakeAIClient):
    """Имитирует модель, которая ошибочно подменяет название разрешённого модуля."""

    def call_ai_json(self, **_kwargs):
        return {
            "course_title": "Python для аналитики",
            "course_goals": "Научиться применять Python в задачах аналитики",
            "target_audience": "middle",
            "modules": [
                {
                    "module_number": 1,
                    "module_title": "Работа с таблицами",
                    "module_goal": "Ошибочно возвращённый модуль.",
                    "lessons": [
                        {
                            "lesson_title": "Pandas",
                            "lesson_goal": "Работать с таблицами.",
                            "content_outline": ["DataFrame"],
                            "assessment": "Практика",
                            "format": "practice",
                            "estimated_time_minutes": 60,
                        }
                    ],
                }
            ],
        }


def _dump(model):
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


def test_course_brief_hides_draft_and_returns_final_outline_after_answers():
    """Черновик не попадает в API-ответ, а прогресс и финал обновляются по ответам."""
    storage = FakeStorage()
    service = CourseBriefService(ai_client=FakeAIClient(), storage=storage)

    started = service.start("Python для аналитики")
    started_payload = _dump(started)
    assert "preliminary_outline" not in started_payload
    assert started.progress.percentage == 0
    assert started.progress.remaining_questions == 2
    assert started.question.number == 1

    lesson_scope = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=started.revision,
            depth=CourseBriefDepth.DEEP,
            knowledge_level=DifficultyLevel.JUNIOR,
            comment="Нужны дополнительные упражнения.",
        ),
    )
    assert lesson_scope.status == CourseBriefStatus.QUESTIONING
    assert lesson_scope.progress.percentage == 0
    assert lesson_scope.question.number == 1
    assert lesson_scope.question.kind.value == "lesson_scope"

    second_module = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=lesson_scope.revision,
            comment="Оставить все",
        ),
    )
    assert second_module.status == CourseBriefStatus.QUESTIONING
    assert second_module.progress.percentage == 50
    assert second_module.question.number == 2

    completed = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=second_module.revision,
            depth=CourseBriefDepth.SKIP,
        ),
    )
    assert completed.status == CourseBriefStatus.COMPLETED
    assert completed.progress.percentage == 100
    assert completed.progress.remaining_questions == 0
    assert completed.question is None
    assert completed.final_course is not None
    assert [module.module_title for module in completed.final_course.modules] == ["Основы Python"]
    assert len(storage.get_course_brief_messages(started.session_id)) >= 6


def test_course_brief_rejects_stale_answer_revision():
    """Повторный ответ от старой вкладки не может перейти к следующему разделу."""
    service = CourseBriefService(ai_client=FakeAIClient(), storage=FakeStorage())
    started = service.start("Python для аналитики")
    service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=started.revision,
            depth=CourseBriefDepth.STANDARD,
            knowledge_level=DifficultyLevel.MIDDLE,
        ),
    )

    try:
        service.answer(
            started.session_id,
            CourseBriefAnswerRequest(
                expected_revision=started.revision,
                depth=CourseBriefDepth.DEEP,
            ),
        )
    except CourseBriefInvalidStateError:
        pass
    else:
        raise AssertionError("Устаревший ответ был принят")


def test_course_brief_never_returns_a_skipped_module_from_ai():
    """Модель не может подменить выбранный пользователем состав модулей."""
    service = CourseBriefService(ai_client=RefiningFakeAIClient(), storage=FakeStorage())
    started = service.start("Python для аналитики")
    lesson_scope = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=started.revision,
            depth=CourseBriefDepth.STANDARD,
            knowledge_level=DifficultyLevel.MIDDLE,
        ),
    )
    second_module = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=lesson_scope.revision,
            comment="Оставить все",
        ),
    )
    completed = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=second_module.revision,
            depth=CourseBriefDepth.SKIP,
        ),
    )

    assert [module.module_title for module in completed.final_course.modules] == ["Основы Python"]
