"""Проверки цикла уточнений Course Brief без сети и БД."""
from typing import Any, Dict, List

from backend.models.domain import (
    CourseBriefAnswerRequest,
    CourseBriefDepth,
    CourseBriefQuestionKind,
    DifficultyLevel,
)
from backend.ai.course_brief_demo_client import CourseBriefDemoClient
from backend.services.course_brief_service import CourseBriefService


class MemoryStorage:
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
        if self.records[brief_id]["revision"] != expected_revision:
            return False
        self.records[brief_id].update(updates)
        return True

    def add_course_brief_message(self, brief_id: str, role: str, content: str, sequence: int):
        self.messages.append(
            {"brief_id": brief_id, "role": role, "content": content, "sequence": sequence}
        )

    def get_course_brief_messages(self, brief_id: str):
        return [item for item in self.messages if item["brief_id"] == brief_id]


class InterviewAI:
    def __init__(self, responses: List[Dict[str, Any]]):
        self.responses = list(responses)
        self.generate_calls: List[Dict[str, Any]] = []

    def generate_course_structure(self, **kwargs):
        self.generate_calls.append(kwargs)
        module_count = int(kwargs.get("module_count") or 2)
        modules = []
        for index in range(1, module_count + 1):
            modules.append(
                {
                    "module_number": index,
                    "module_title": f"Раздел {index}",
                    "module_goal": "Понять основу.",
                    "lessons": [
                        {
                            "lesson_title": "Основы" if index == 1 else f"Практика {index}",
                            "lesson_goal": "Разобраться.",
                            "estimated_time_minutes": 30,
                        }
                    ],
                }
            )
        # Для сценариев anti-dup оставляем узнаваемые названия первых двух.
        if module_count >= 2:
            modules[0]["module_title"] = "Первый раздел"
            modules[0]["lessons"][0]["lesson_title"] = "Основы"
            modules[1]["module_title"] = "Второй раздел"
            modules[1]["lessons"][0]["lesson_title"] = "Практика"
        return {
            "course_title": "Курс",
            "course_goals": kwargs["course_goals"],
            "target_audience": kwargs.get("audience_level") or "middle",
            "modules": modules,
        }

    def call_ai_json(self, **_kwargs):
        return self.responses.pop(0) if self.responses else None


def _signals(necessity, depth, knowledge, application, scope=None):
    return {
        "necessity": necessity,
        "depth": depth,
        "knowledge": knowledge,
        "application": application,
        "scope": scope or _missing(),
    }


def _confirmed(value, evidence=None):
    return {"status": "confirmed", "value": value, "evidence": evidence or []}


def _missing():
    return {"status": "missing", "value": None, "evidence": []}


def _not_applicable():
    return {"status": "not_applicable", "value": None, "evidence": []}


def _excluded_result(action, question=None):
    return {
        "signals": _signals(
            _confirmed("exclude"),
            _not_applicable(),
            _not_applicable(),
            _not_applicable(),
            _not_applicable(),
        ),
        "action": action,
        "follow_up_question": question,
    }


def test_model_follow_up_keeps_module_and_persists_unique_messages():
    ai = InterviewAI(
        [
            {
                "signals": _signals(
                    _confirmed("include"),
                    _confirmed("standard"),
                    _missing(),
                    _missing(),
                ),
                "action": "ask",
                "follow_up_question": "Каков ваш текущий опыт в этой теме?",
            },
            {
                "signals": _signals(
                    _confirmed("include", ["В рабочем объёме"]),
                    _confirmed("standard", ["В рабочем объёме"]),
                    _confirmed("junior", ["Я начинающий"]),
                    _missing(),
                    _missing(),
                ),
                "action": "next_module",
                "follow_up_question": None,
            },
        ]
    )
    storage = MemoryStorage()
    service = CourseBriefService(ai_client=ai, storage=storage)
    started = service.start("Тема", module_count=2)

    follow_up = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=started.revision,
            depth=CourseBriefDepth.STANDARD,
        ),
    )
    assert follow_up.question.number == 1
    assert follow_up.question.kind == CourseBriefQuestionKind.FOLLOW_UP
    assert follow_up.question.text == "Каков ваш текущий опыт в этой теме?"
    assert follow_up.progress.percentage == 0
    assert follow_up.confidence.current_module_percentage == 50
    assert follow_up.confidence.structure_percentage == 25

    lesson_scope = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=follow_up.revision,
            comment="Я начинающий.",
        ),
    )
    assert lesson_scope.question.number == 1
    assert lesson_scope.question.kind == CourseBriefQuestionKind.LESSON_SCOPE
    assert "Основы" in lesson_scope.question.text
    decision = storage.records[started.session_id]["decisions"][0]
    assert decision["finalized"] is False
    assert decision["phase"] == "lesson_scope"
    assert decision["signals"]["knowledge"]["value"] == "junior"

    # «Оставить все» подтверждает состав и пропускает extras (если нет deferred).
    next_module = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=lesson_scope.revision,
            comment="Оставить все уроки.",
        ),
    )
    assert next_module.question.number == 2
    assert next_module.question.kind == CourseBriefQuestionKind.MODULE
    assert next_module.progress.percentage == 50
    decision = storage.records[started.session_id]["decisions"][0]
    assert decision["finalized"] is True
    assert decision["phase"] == "done"
    assert decision["signals"]["scope"]["value"] == "whole"


def test_all_excluded_requests_goal_and_restarts_same_session():
    ai = InterviewAI(
        [
            _excluded_result("next_module"),
            _excluded_result(
                "revise_goal",
                "Какую основную цель вы хотите достичь с помощью курса?",
            ),
        ]
    )
    storage = MemoryStorage()
    service = CourseBriefService(ai_client=ai, storage=storage)
    started = service.start("Тема", module_count=2)

    second = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(expected_revision=started.revision, depth=CourseBriefDepth.SKIP),
    )
    revise_goal = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(expected_revision=second.revision, depth=CourseBriefDepth.SKIP),
    )
    assert revise_goal.question.kind == CourseBriefQuestionKind.REVISE_GOAL
    assert revise_goal.progress.percentage == 50

    restarted = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=revise_goal.revision,
            comment="Научиться собирать отчёты для отдела продаж.",
        ),
    )
    assert restarted.session_id == started.session_id
    assert restarted.question.number == 1
    assert restarted.question.kind == CourseBriefQuestionKind.MODULE
    assert restarted.progress.percentage == 0
    assert storage.records[started.session_id]["decisions"] == []
    assert ai.generate_calls[-1]["course_goals"] == "Научиться собирать отчёты для отдела продаж."


def test_demo_fallback_asks_on_text_only_answer_without_network():
    storage = MemoryStorage()
    service = CourseBriefService(ai_client=CourseBriefDemoClient(), storage=storage)
    started = service.start("Тема", module_count=2)

    follow_up = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=started.revision,
            comment="Пока не уверен, пригодится ли это в моей работе.",
        ),
    )

    assert follow_up.question.number == 1
    assert follow_up.question.kind == CourseBriefQuestionKind.FOLLOW_UP
    assert follow_up.progress.percentage == 0
    assert "включить" in follow_up.question.text
    decision = storage.records[started.session_id]["decisions"][0]
    assert decision["followup_count"] == 1
    assert decision["signals"]["necessity"]["status"] == "missing"


def test_add_module_asks_then_inserts_and_recounts_questions():
    """Запрос нового раздела уточняется, затем модуль попадает в черновик."""
    ai = InterviewAI(
        [
            {
                "signals": _signals(
                    _confirmed("include"),
                    _confirmed("standard"),
                    _missing(),
                    _missing(),
                    _missing(),
                ),
                "action": "ask",
                "follow_up_question": "Что должно войти в раздел «оконные функции» и зачем он вам нужен?",
                "structure_request": {
                    "kind": "add_module",
                    "title": "оконные функции",
                    "purpose": None,
                    "ready": False,
                    "evidence": ["Добавьте модуль про оконные функции"],
                },
            },
            {
                "signals": _signals(
                    _confirmed("include", ["В рабочем объёме"]),
                    _confirmed("standard", ["В рабочем объёме"]),
                    _confirmed("middle", ["Для аналитики отчётов"]),
                    _missing(),
                    _confirmed("whole", ["все темы текущего раздела"]),
                ),
                "action": "next_module",
                "follow_up_question": None,
                "structure_request": {
                    "kind": "add_module",
                    "title": "оконные функции",
                    "purpose": "Для аналитики отчётов",
                    "ready": True,
                    "evidence": ["Для аналитики отчётов"],
                },
            },
        ]
    )
    storage = MemoryStorage()
    service = CourseBriefService(ai_client=ai, storage=storage)
    started = service.start("Тема", module_count=2)
    assert started.progress.total_questions == 2

    clarifying = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=started.revision,
            depth=CourseBriefDepth.STANDARD,
            comment="Добавьте модуль про оконные функции",
        ),
    )
    assert clarifying.question.kind == CourseBriefQuestionKind.ADD_MODULE
    assert clarifying.progress.total_questions == 2
    assert clarifying.question.number == 1

    after_insert = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=clarifying.revision,
            comment="Для аналитики отчётов, все темы текущего раздела",
        ),
    )
    assert after_insert.progress.total_questions == 3
    assert after_insert.question.kind == CourseBriefQuestionKind.LESSON_SCOPE
    assert after_insert.question.number == 1
    titles = [
        module["module_title"]
        for module in storage.records[started.session_id]["preliminary_outline"]["modules"]
    ]
    assert titles == ["Первый раздел", "оконные функции", "Второй раздел"]


def test_demo_fallback_detects_add_module_request_from_comment():
    storage = MemoryStorage()
    service = CourseBriefService(ai_client=CourseBriefDemoClient(), storage=storage)
    started = service.start("Тема", module_count=2)
    clarifying = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=started.revision,
            comment="Добавьте модуль про оконные функции",
        ),
    )
    assert clarifying.question.kind == CourseBriefQuestionKind.ADD_MODULE
    assert "оконные функции" in clarifying.question.text


def test_included_module_enters_lesson_scope_with_listed_lessons():
    """После gate включённого модуля опрос переходит к черновику уроков."""
    ai = InterviewAI(
        [
            {
                "signals": _signals(
                    _confirmed("include"),
                    _confirmed("standard"),
                    _missing(),
                    _missing(),
                    _missing(),
                ),
                "action": "ask",
                "follow_up_question": "Хотите ли вы изучить все темы раздела «сортировка»?",
            },
        ]
    )
    storage = MemoryStorage()
    service = CourseBriefService(ai_client=ai, storage=storage)
    started = service.start("Тема", module_count=2)
    lesson_scope = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=started.revision,
            depth=CourseBriefDepth.STANDARD,
            knowledge_level=DifficultyLevel.MIDDLE,
            comment="группировка с использованием HAVING",
        ),
    )
    assert lesson_scope.question.kind == CourseBriefQuestionKind.LESSON_SCOPE
    assert "Основы" in lesson_scope.question.text
    assert "«" in lesson_scope.question.text
    decision = storage.records[started.session_id]["decisions"][0]
    assert decision["signals"]["knowledge"]["value"] == "middle"
    assert decision["phase"] == "lesson_scope"
    assert decision["finalized"] is False


def test_comment_declines_extras_does_not_match_urok_substring():
    """«ок» внутри «урок» не должно пропускать extras."""
    from backend.services.course_brief_interview import (
        comment_declines_extras,
        lesson_scope_question,
    )

    assert comment_declines_extras("ок") is True
    assert comment_declines_extras("хорошо") is True
    assert comment_declines_extras("урок про JOIN") is False
    assert comment_declines_extras("добавить урок про окна") is False
    assert comment_declines_extras("оставить все") is True

    many = [f"Урок {index}" for index in range(1, 10)]
    text = lesson_scope_question("Блок", many)
    for title in many:
        assert f"«{title}»" in text
    assert "Всего в черновике: 9" in text


def test_demo_fallback_splits_module_from_comment():
    """Разделение текущего блока увеличивает N и возвращает к module_gate."""
    storage = MemoryStorage()
    service = CourseBriefService(ai_client=CourseBriefDemoClient(), storage=storage)
    started = service.start("Тема", module_count=2)
    initial_total = started.progress.total_questions
    clarifying = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=started.revision,
            comment="Раздели на теорию SQL и практику SQL",
        ),
    )
    # Либо сразу split (если оба названия извлечены), либо уточнение.
    if clarifying.question.kind == CourseBriefQuestionKind.SPLIT_MODULE:
        clarifying = service.answer(
            started.session_id,
            CourseBriefAnswerRequest(
                expected_revision=clarifying.revision,
                comment="теория SQL и практика SQL",
            ),
        )
    assert clarifying.progress.total_questions == initial_total + 1
    assert clarifying.question.kind == CourseBriefQuestionKind.MODULE
    assert clarifying.question.number == 1
    titles = [
        module["module_title"]
        for module in storage.records[started.session_id]["preliminary_outline"]["modules"]
    ]
    assert len(titles) == initial_total + 1
    assert any("теор" in title.lower() or "sql" in title.lower() for title in titles[:2])
    assert "Разделил блок" in clarifying.question.text


def test_lesson_extras_dedups_topics_from_other_modules():
    """Дубликаты тем других блоков откладываются, уникальные добавляются."""
    ai = InterviewAI(
        [
            {
                "signals": _signals(
                    _confirmed("include"),
                    _confirmed("standard"),
                    _confirmed("middle"),
                    _missing(),
                    _missing(),
                ),
                "action": "next_module",
                "follow_up_question": None,
            },
        ]
    )
    storage = MemoryStorage()
    service = CourseBriefService(ai_client=ai, storage=storage)
    started = service.start("Тема", module_count=2)
    scope = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=started.revision,
            depth=CourseBriefDepth.STANDARD,
            knowledge_level=DifficultyLevel.MIDDLE,
        ),
    )
    assert scope.question.kind == CourseBriefQuestionKind.LESSON_SCOPE
    # Комментарий без decline-фразы — спрашиваем extras.
    extras = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=scope.revision,
            comment="Оставить текущий список уроков",
        ),
    )
    assert extras.question.kind == CourseBriefQuestionKind.LESSON_EXTRAS
    next_module = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=extras.revision,
            comment="Практика, оконные функции",
        ),
    )
    assert next_module.question.kind == CourseBriefQuestionKind.MODULE
    decision = storage.records[started.session_id]["decisions"][0]
    assert "оконные функции" in (decision.get("extra_topics") or []) or any(
        item.get("title") == "оконные функции"
        for item in (decision.get("lesson_decisions") or [])
    )
    # «Практика» совпадает с уроком второго модуля → deferred
    deferred = storage.records[started.session_id].get("deferred_topics") or []
    assert any(
        (item.get("existing_title") or item.get("title") or "").lower() == "практика"
        or (item.get("title") or "").lower() == "практика"
        for item in deferred
    )


def test_prebrief_params_drive_draft_generation():
    """Pre-brief цель/уровень/объём передаются в generate_course_structure и brief_meta."""
    storage = MemoryStorage()
    ai = InterviewAI([])
    service = CourseBriefService(ai_client=ai, storage=storage)
    started = service.start(
        "SQL для аналитиков",
        course_goals="Научиться писать отчёты",
        audience_level="junior",
        module_count=3,
    )
    assert started.progress.total_questions == 3
    assert ai.generate_calls
    call = ai.generate_calls[0]
    assert call["course_goals"] == "Научиться писать отчёты"
    assert call["audience_level"] == "junior"
    assert call["module_count"] == 3
    meta = storage.records[started.session_id]["brief_meta"]
    assert meta["course_goals"] == "Научиться писать отчёты"
    assert meta["audience_level"] == "junior"
    assert meta["module_count"] == 3


def test_lesson_draft_dedups_topics_from_other_modules():
    """После L' дубликаты уроков убираются и пишутся в deferred_topics."""
    ai = InterviewAI(
        [
            {
                "signals": _signals(
                    _confirmed("include"),
                    _confirmed("standard"),
                    _confirmed("middle"),
                    _missing(),
                    _missing(),
                ),
                "action": "next_module",
                "follow_up_question": None,
            },
        ]
    )
    storage = MemoryStorage()
    service = CourseBriefService(ai_client=ai, storage=storage)
    started = service.start("Тема", module_count=2)
    # Первый модуль без уроков, второй уже содержит «Практика» — L' вернёт дубль.
    outline = storage.records[started.session_id]["preliminary_outline"]
    outline["modules"][0]["lessons"] = []
    outline["modules"][1]["lessons"] = [
        {
            "lesson_title": "Практика",
            "lesson_goal": "Применить.",
            "content_outline": ["Задание"],
            "assessment": "Практика",
            "format": "practice",
            "estimated_time_minutes": 30,
        }
    ]
    storage.records[started.session_id]["preliminary_outline"] = outline

    # Подменяем call_ai_json на генерацию уроков с дублем.
    def lesson_draft(**_kwargs):
        return {
            "lessons": [
                {
                    "lesson_title": "Практика",
                    "lesson_goal": "Дубль.",
                    "content_outline": ["A"],
                    "assessment": "Практика",
                    "format": "practice",
                    "estimated_time_minutes": 30,
                },
                {
                    "lesson_title": "HAVING",
                    "lesson_goal": "Уникальная тема.",
                    "content_outline": ["B"],
                    "assessment": "Практика",
                    "format": "theory",
                    "estimated_time_minutes": 30,
                },
            ]
        }

    ai.call_ai_json = lesson_draft
    scope = service.answer(
        started.session_id,
        CourseBriefAnswerRequest(
            expected_revision=started.revision,
            depth=CourseBriefDepth.STANDARD,
            knowledge_level=DifficultyLevel.MIDDLE,
        ),
    )
    assert scope.question.kind == CourseBriefQuestionKind.LESSON_SCOPE
    titles = [
        lesson["lesson_title"]
        for lesson in storage.records[started.session_id]["preliminary_outline"]["modules"][0][
            "lessons"
        ]
    ]
    assert "Практика" not in titles
    assert "HAVING" in titles
    deferred = storage.records[started.session_id].get("deferred_topics") or []
    assert any((item.get("title") or "").lower() == "практика" for item in deferred)
