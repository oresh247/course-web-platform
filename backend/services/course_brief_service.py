"""Сервис интервью для поэтапного уточнения структуры будущего курса.

Черновой outline и сообщения сохраняются отдельно от опубликованных курсов.
Это позволяет приостановить интервью на ответе пользователя и не передавать
промежуточную структуру в браузер.
"""
import json
import logging
import math
from typing import Any, Dict, List, Optional
from uuid import uuid4

from backend.ai.prompts import (
    COURSE_BRIEF_INTERVIEW_PROMPT_TEMPLATE,
    COURSE_BRIEF_INTERVIEW_SYSTEM_PROMPT,
    COURSE_BRIEF_LESSON_DRAFT_PROMPT_TEMPLATE,
    COURSE_BRIEF_LESSON_DRAFT_SYSTEM_PROMPT,
    COURSE_BRIEF_REFINEMENT_PROMPT_TEMPLATE,
    COURSE_BRIEF_REFINEMENT_SYSTEM_PROMPT,
)
from backend.database import db
from backend.models.domain import (
    Course,
    CourseBriefAnswerControls,
    CourseBriefAnswerRequest,
    CourseBriefChatMessage,
    CourseBriefConfidence,
    CourseBriefDepth,
    CourseBriefProgress,
    CourseBriefQuestion,
    CourseBriefQuestionKind,
    CourseBriefResponse,
    CourseBriefStatus,
    DifficultyLevel,
    Lesson,
    LessonFormat,
    Module,
)
from backend.services.course_brief_interview import (
    CourseBriefInterviewAction,
    CourseBriefInterviewResult,
    CourseBriefInterviewSignal,
    CourseBriefInterviewSignals,
    CourseBriefSignalStatus,
    CourseBriefStructureChangeKind,
    MAX_ADD_MODULE_FOLLOWUPS,
    MAX_LESSON_PHASE_FOLLOWUPS,
    MAX_MODULE_FOLLOWUPS,
    MODULE_GATE_SIGNALS,
    PHASE_DONE,
    PHASE_LESSON_EXTRAS,
    PHASE_LESSON_SCOPE,
    PHASE_MODULE_GATE,
    add_module_question,
    apply_answer_buttons_to_signals,
    apply_comment_hints_to_signals,
    build_lesson_decisions,
    choose_add_module_action,
    choose_server_action,
    collect_other_module_topics,
    comment_declines_extras,
    confidence_from_signals,
    course_brief_interview_json_schema,
    clarifying_reply_for_lessons,
    default_question_for_missing,
    extract_requested_topics,
    find_duplicate_topics,
    infer_structure_request_from_comment,
    is_clarifying_question,
    is_vague_topic_question,
    lesson_extras_question,
    lesson_scope_question,
    make_fallback_result,
    match_lesson_by_comment,
    merge_lesson_promises,
    merge_signals,
    merge_structure_request,
    model_dump as dump_interview_model,
    module_is_included,
    parse_excluded_lessons_from_comment,
    parse_extra_topics_from_comment,
    primary_missing_signal,
    scope_question_for_lessons,
    signals_to_dict,
    snapshot_lesson_promise,
    validate_interview_result,
)

logger = logging.getLogger(__name__)


class CourseBriefNotFoundError(Exception):
    """Сессия интервью не найдена."""


class CourseBriefInvalidStateError(Exception):
    """Действие не соответствует текущему состоянию интервью."""


class CourseBriefGenerationError(Exception):
    """Не удалось сформировать или уточнить структуру с помощью AI."""


class CourseBriefService:
    """Оркестрирует черновик, интервью и финальное уточнение структуры."""

    DEFAULT_MODULE_COUNT = 4
    DEFAULT_AUDIENCE_LEVEL = DifficultyLevel.MIDDLE.value
    DEFAULT_DURATION_WEEKS = 4
    DEFAULT_HOURS_PER_WEEK = 3

    def __init__(self, ai_client: Optional[Any] = None, storage: Optional[Any] = None):
        """Создаёт сервис с ленивым AI-клиентом и заменяемым хранилищем для тестов."""
        self._ai_client = ai_client
        self._storage = storage or db

    def start(self, topic: str) -> CourseBriefResponse:
        """Создаёт скрытый черновик и возвращает пользователю первый вопрос."""
        try:
            draft_data = self._get_ai_client().generate_course_structure(
                topic=topic,
                audience_level=self.DEFAULT_AUDIENCE_LEVEL,
                module_count=self.DEFAULT_MODULE_COUNT,
                course_goals="Цели и глубина проработки уточняются в диалоге.",
                duration_weeks=self.DEFAULT_DURATION_WEEKS,
                hours_per_week=self.DEFAULT_HOURS_PER_WEEK,
            )
        except Exception as error:
            logger.exception("Не удалось сформировать черновик структуры курса")
            raise CourseBriefGenerationError("Не удалось сформировать черновик структуры курса") from error

        if not draft_data:
            raise CourseBriefGenerationError("Модель не вернула черновик структуры курса")

        try:
            draft_course = Course(**draft_data)
        except Exception as error:
            logger.exception("Модель вернула некорректный черновик структуры курса")
            raise CourseBriefGenerationError("Модель вернула некорректную структуру курса") from error

        if not draft_course.modules:
            raise CourseBriefGenerationError("В черновике структуры нет разделов для уточнения")

        session_id = str(uuid4())
        total_questions = len(draft_course.modules)
        record = {
            "id": session_id,
            "topic": topic,
            "status": CourseBriefStatus.QUESTIONING.value,
            "preliminary_outline": self._dump_model(draft_course),
            "decisions": [],
            "current_question_index": 0,
            "total_questions": total_questions,
            "final_outline": None,
            "revision": 1,
        }
        self._storage.create_course_brief(record)
        self._storage.add_course_brief_message(session_id, "user", topic, 1)
        self._storage.add_course_brief_message(
            session_id,
            "assistant",
            self._build_question(draft_course, 0).text,
            2,
        )
        logger.info("✅ Запущено интервью по структуре курса: %s", session_id)
        return self._build_response(record)

    def get_state(self, session_id: str) -> CourseBriefResponse:
        """Возвращает безопасное состояние сохранённой сессии без чернового outline."""
        return self._build_response(self._get_record(session_id))

    def answer(
        self,
        session_id: str,
        answer: CourseBriefAnswerRequest,
    ) -> CourseBriefResponse:
        """Интерпретирует ответ и при необходимости остаётся на текущем модуле."""
        record = self._get_record(session_id)
        if record.get("status") != CourseBriefStatus.QUESTIONING.value:
            raise CourseBriefInvalidStateError("Интервью уже завершено")

        current_revision = int(record.get("revision") or 1)
        if answer.expected_revision != current_revision:
            raise CourseBriefInvalidStateError(
                "Сессия уже изменилась. Обновите страницу перед отправкой ответа."
            )

        draft_course = Course(**self._load_json(record.get("preliminary_outline"), {}))
        current_index = int(record.get("current_question_index") or 0)
        if current_index >= len(draft_course.modules):
            raise CourseBriefInvalidStateError("В интервью больше нет вопросов")

        decisions = self._load_json(record.get("decisions"), [])
        if not isinstance(decisions, list):
            raise CourseBriefInvalidStateError("Сохранённые решения имеют неверный формат")

        module = draft_course.modules[current_index]
        current_decision = self._decision_for_module(decisions, module.module_number)
        if self._pending_question_kind(current_decision) == CourseBriefQuestionKind.REVISE_GOAL.value:
            return self._restart_after_revised_goal(
                record=record,
                answer=answer,
                current_revision=current_revision,
            )

        phase = self._module_phase(current_decision)
        if phase == PHASE_LESSON_SCOPE:
            return self._answer_lesson_scope_phase(
                record=record,
                answer=answer,
                current_revision=current_revision,
                draft_course=draft_course,
                current_index=current_index,
                decisions=decisions,
                current_decision=current_decision,
            )
        if phase == PHASE_LESSON_EXTRAS:
            return self._answer_lesson_extras_phase(
                record=record,
                answer=answer,
                current_revision=current_revision,
                draft_course=draft_course,
                current_index=current_index,
                decisions=decisions,
                current_decision=current_decision,
            )

        history = self._decision_history(current_decision)
        included_before_current = self._included_modules(decisions, module.module_number)
        lesson_titles = [lesson.lesson_title for lesson in module.lessons]
        pending_structure_change = (
            current_decision.get("pending_structure_change") if current_decision else None
        )
        other_topics = collect_other_module_topics(draft_course.modules, module.module_number)
        interview_result, used_fallback = self._interpret_module_answer(
            topic=record["topic"],
            module=module,
            total_modules=len(draft_course.modules),
            completed_modules=self._completed_modules(decisions, module.module_number),
            included_modules=included_before_current,
            history=history,
            answer=answer,
            followup_count=self._followup_count(current_decision),
            pending_structure_change=pending_structure_change,
            phase=PHASE_MODULE_GATE,
            other_modules_topics=other_topics,
        )
        if interview_result.structure_request.kind == CourseBriefStructureChangeKind.NONE:
            inferred_request = infer_structure_request_from_comment(answer.comment)
            if inferred_request.kind == CourseBriefStructureChangeKind.ADD_MODULE:
                interview_result.structure_request = inferred_request
        structure_request = merge_structure_request(
            pending_structure_change,
            interview_result.structure_request,
        )
        add_followup_count = self._structure_followup_count(pending_structure_change)
        structure_action = choose_add_module_action(
            structure_request,
            add_followup_count,
            (item.module_title for item in draft_course.modules),
        )

        inserted_module_title = None
        if structure_action == "insert":
            inserted_number = current_index + 2
            draft_course = self._insert_requested_module(
                draft_course,
                current_index,
                structure_request,
                record["topic"],
            )
            decisions = self._shift_decisions_after_insert(decisions, inserted_number)
            inserted_module_title = (structure_request.title or "").strip()
            structure_request = None
            pending_structure_change = None
            module = draft_course.modules[current_index]
            lesson_titles = [lesson.lesson_title for lesson in module.lessons]

        signals = merge_signals(
            current_decision.get("signals") if current_decision else None,
            interview_result.signals,
        )
        signals = apply_answer_buttons_to_signals(signals, answer)
        signals = apply_comment_hints_to_signals(signals, answer.comment)
        followup_count = self._followup_count(current_decision)
        action = choose_server_action(
            signals=signals,
            followup_count=followup_count,
            max_followups=MAX_MODULE_FOLLOWUPS,
            is_last_module=current_index == len(draft_course.modules) - 1,
            included_modules_before_current=included_before_current,
            critical_signals=MODULE_GATE_SIGNALS,
        )
        # В demo/fallback-режиме выбранная кнопка остаётся достаточным решением
        # по module_gate. Полнота сигналов всё равно видна в confidence, но локальный
        # сценарий не требует сети и не застревает на каждом вопросе.
        if (
            structure_action != "ask"
            and used_fallback
            and answer.depth is not None
            and action == CourseBriefInterviewAction.ASK
        ):
            action = choose_server_action(
                signals=signals,
                followup_count=MAX_MODULE_FOLLOWUPS,
                max_followups=MAX_MODULE_FOLLOWUPS,
                is_last_module=current_index == len(draft_course.modules) - 1,
                included_modules_before_current=included_before_current,
                critical_signals=MODULE_GATE_SIGNALS,
            )

        pending_question = None
        pending_kind = None
        pending_answer_controls = None
        stored_structure_change = None
        decision_phase = PHASE_MODULE_GATE
        if structure_action == "ask":
            add_followup_count += 1
            pending_question = self._select_add_module_question(
                interview_result,
                structure_request,
            )
            pending_kind = CourseBriefQuestionKind.ADD_MODULE.value
            pending_answer_controls = CourseBriefAnswerControls.TEXT.value
            stored_structure_change = {
                **dump_interview_model(structure_request),
                "followup_count": add_followup_count,
            }
            action = CourseBriefInterviewAction.ASK
        elif action == CourseBriefInterviewAction.ASK:
            followup_count += 1
            pending_question = self._select_follow_up_question(
                interview_result,
                signals,
                CourseBriefQuestionKind.FOLLOW_UP,
                lesson_titles=lesson_titles,
                comment=answer.comment,
            )
            pending_kind = CourseBriefQuestionKind.FOLLOW_UP.value
            gap = primary_missing_signal(signals, MODULE_GATE_SIGNALS)
            if gap == "knowledge":
                pending_answer_controls = CourseBriefAnswerControls.KNOWLEDGE.value
            elif gap in {"depth", "necessity"}:
                pending_answer_controls = CourseBriefAnswerControls.DEPTH.value
            else:
                pending_answer_controls = CourseBriefAnswerControls.TEXT.value
        elif action == CourseBriefInterviewAction.REVISE_GOAL:
            pending_question = self._select_follow_up_question(
                interview_result,
                signals,
                CourseBriefQuestionKind.REVISE_GOAL,
                lesson_titles=lesson_titles,
                comment=answer.comment,
            )
            pending_kind = CourseBriefQuestionKind.REVISE_GOAL.value
            pending_answer_controls = CourseBriefAnswerControls.TEXT.value
        elif module_is_included(signals):
            # Включённый блок: сначала черновик уроков, потом extras, финал в конце.
            draft_course = self._ensure_module_lesson_draft(
                draft_course,
                current_index,
                topic=record["topic"],
                depth=self._decision_depth(signals, answer),
                knowledge_level=self._decision_knowledge_level(signals, answer),
            )
            module = draft_course.modules[current_index]
            lesson_titles = [lesson.lesson_title for lesson in module.lessons]
            pending_question = lesson_scope_question(
                module.module_title,
                lesson_titles,
                knowledge_level=self._decision_knowledge_level(signals, answer),
            )
            pending_kind = CourseBriefQuestionKind.LESSON_SCOPE.value
            pending_answer_controls = CourseBriefAnswerControls.TEXT.value
            decision_phase = PHASE_LESSON_SCOPE
            action = CourseBriefInterviewAction.ASK

        user_message = self._format_answer_message(answer)
        updated_history = [*history, {"role": "user", "content": user_message}]
        if pending_question:
            updated_history.append({"role": "assistant", "content": pending_question})

        decision = {
            "module_number": module.module_number,
            "module_title": module.module_title,
            "depth": self._decision_depth(signals, answer),
            "knowledge_level": self._decision_knowledge_level(signals, answer),
            "comment": (answer.comment or "").strip() or None,
            "signals": signals_to_dict(signals),
            "followup_count": followup_count,
            "lesson_followup_count": 0,
            "history": updated_history,
            "confidence_percentage": confidence_from_signals(signals_to_dict(signals))[0],
            "phase": decision_phase,
            "finalized": action in {
                CourseBriefInterviewAction.NEXT_MODULE,
                CourseBriefInterviewAction.FINISH,
            }
            and decision_phase == PHASE_MODULE_GATE,
            "pending_question": pending_question,
            "pending_question_kind": pending_kind,
            "pending_answer_controls": pending_answer_controls,
            "pending_structure_change": stored_structure_change,
            "lesson_decisions": (
                current_decision.get("lesson_decisions") if current_decision else None
            ),
            "extra_topics": current_decision.get("extra_topics") if current_decision else None,
        }
        decisions = self._upsert_decision(decisions, decision)

        revision = current_revision + 1
        updates: Dict[str, Any] = {
            "decisions": decisions,
            "revision": revision,
            "total_questions": len(draft_course.modules),
            "preliminary_outline": self._dump_model(draft_course),
        }
        if action == CourseBriefInterviewAction.ASK:
            updates["current_question_index"] = current_index
            assistant_message = pending_question or default_question_for_missing(
                signals,
                lesson_titles,
            )
            if inserted_module_title:
                assistant_message = (
                    f"Добавил в план раздел «{inserted_module_title}». {assistant_message}"
                )
        elif action == CourseBriefInterviewAction.REVISE_GOAL:
            updates["current_question_index"] = current_index
            assistant_message = pending_question or self._fallback_revise_goal_question()
        elif action == CourseBriefInterviewAction.FINISH:
            final_course = self._refine_outline(draft_course, decisions, record["topic"])
            updates.update(
                {
                    "status": CourseBriefStatus.COMPLETED.value,
                    "final_outline": self._dump_model(final_course),
                    "current_question_index": len(draft_course.modules),
                }
            )
            assistant_message = "Спасибо, уточнения собраны. Финальная структура курса готова."
        else:
            next_index = current_index + 1
            updates["current_question_index"] = next_index
            assistant_message = self._build_question(draft_course, next_index).text
            if inserted_module_title:
                assistant_message = (
                    f"Добавил в план раздел «{inserted_module_title}». {assistant_message}"
                )

        if not self._storage.update_course_brief(
            session_id,
            updates,
            expected_revision=answer.expected_revision,
        ):
            raise CourseBriefInvalidStateError(
                "Сессия уже изменилась. Обновите страницу перед отправкой ответа."
            )
        message_sequence = self._next_message_sequence(session_id)
        self._storage.add_course_brief_message(
            session_id,
            "user",
            self._format_answer_message(answer),
            message_sequence,
        )
        self._storage.add_course_brief_message(
            session_id,
            "assistant",
            assistant_message,
            message_sequence + 1,
        )
        updated_record = {**record, **updates}
        return self._build_response(updated_record)

    def _answer_lesson_scope_phase(
        self,
        *,
        record: Dict[str, Any],
        answer: CourseBriefAnswerRequest,
        current_revision: int,
        draft_course: Course,
        current_index: int,
        decisions: List[Dict[str, Any]],
        current_decision: Optional[Dict[str, Any]],
    ) -> CourseBriefResponse:
        """Уточняет состав уроков текущего модуля и переходит к extras."""
        module = draft_course.modules[current_index]
        history = self._decision_history(current_decision)
        lesson_titles = [lesson.lesson_title for lesson in module.lessons]
        comment = (answer.comment or "").strip()

        if is_clarifying_question(comment):
            return self._answer_lesson_clarification(
                record=record,
                answer=answer,
                current_revision=current_revision,
                draft_course=draft_course,
                current_index=current_index,
                decisions=decisions,
                current_decision=current_decision,
                history=history,
                phase=PHASE_LESSON_SCOPE,
                pending_kind=CourseBriefQuestionKind.LESSON_SCOPE.value,
                follow_up_question=lesson_scope_question(
                    module.module_title,
                    lesson_titles,
                    knowledge_level=(current_decision or {}).get("knowledge_level"),
                ),
            )

        excluded = parse_excluded_lessons_from_comment(comment, lesson_titles)
        scope_value = "partial" if excluded else "whole"
        if comment and any(
            token in comment.lower()
            for token in ("убр", "исключ", "замен", "только ", "кроме")
        ) and not excluded:
            # Нужно уточнение: назвал правки, но не сопоставили с уроками.
            lesson_followups = int((current_decision or {}).get("lesson_followup_count") or 0)
            if lesson_followups < MAX_LESSON_PHASE_FOLLOWUPS:
                pending_question = lesson_scope_question(
                    module.module_title,
                    lesson_titles,
                    knowledge_level=(current_decision or {}).get("knowledge_level"),
                )
                return self._persist_lesson_phase_step(
                    record=record,
                    answer=answer,
                    current_revision=current_revision,
                    draft_course=draft_course,
                    current_index=current_index,
                    decisions=decisions,
                    current_decision=current_decision,
                    history=history,
                    phase=PHASE_LESSON_SCOPE,
                    pending_question=pending_question,
                    pending_kind=CourseBriefQuestionKind.LESSON_SCOPE.value,
                    lesson_followup_count=lesson_followups + 1,
                    signals_patch=None,
                    lesson_decisions=None,
                    extra_topics=None,
                    finalize=False,
                    deferred_topics=None,
                )

        lesson_decisions = build_lesson_decisions(
            lesson_titles,
            excluded=excluded,
            knowledge_level=(current_decision or {}).get("knowledge_level"),
            comment=comment or None,
        )
        try:
            signals = CourseBriefInterviewSignals.model_validate(
                (current_decision or {}).get("signals") or {}
            )
        except Exception:
            signals = make_fallback_result(answer).signals
        signals.scope = CourseBriefInterviewSignal(
            status=CourseBriefSignalStatus.CONFIRMED,
            value=scope_value,
            evidence=[comment] if comment else [],
        )

        deferred_for_module = self._deferred_topics_for_module(
            record,
            module.module_number,
        )
        # Если состав уже подтверждён и пользователь явно отказался от добавок —
        # не спрашиваем то же самое второй раз (кроме отложенных тем с других блоков).
        if comment_declines_extras(comment) and not deferred_for_module:
            is_last = current_index >= len(draft_course.modules) - 1
            return self._persist_lesson_phase_step(
                record=record,
                answer=answer,
                current_revision=current_revision,
                draft_course=draft_course,
                current_index=current_index,
                decisions=decisions,
                current_decision=current_decision,
                history=history,
                phase=PHASE_DONE,
                pending_question=None,
                pending_kind=None,
                lesson_followup_count=0,
                signals_patch=signals_to_dict(signals),
                lesson_decisions=lesson_decisions,
                extra_topics=[],
                finalize=True,
                deferred_topics=None,
                finish_course=is_last,
            )

        other_topics = collect_other_module_topics(draft_course.modules, module.module_number)
        pending_question = lesson_extras_question(module.module_title, other_topics)
        if deferred_for_module:
            titles = ", ".join(
                f"«{item['title']}»" for item in deferred_for_module[:4] if item.get("title")
            )
            pending_question = (
                f"Ранее для этого блока отложили темы: {titles}. "
                + pending_question
            )

        return self._persist_lesson_phase_step(
            record=record,
            answer=answer,
            current_revision=current_revision,
            draft_course=draft_course,
            current_index=current_index,
            decisions=decisions,
            current_decision=current_decision,
            history=history,
            phase=PHASE_LESSON_EXTRAS,
            pending_question=pending_question,
            pending_kind=CourseBriefQuestionKind.LESSON_EXTRAS.value,
            lesson_followup_count=0,
            signals_patch=signals_to_dict(signals),
            lesson_decisions=lesson_decisions,
            extra_topics=None,
            finalize=False,
            deferred_topics=None,
        )

    def _answer_lesson_extras_phase(
        self,
        *,
        record: Dict[str, Any],
        answer: CourseBriefAnswerRequest,
        current_revision: int,
        draft_course: Course,
        current_index: int,
        decisions: List[Dict[str, Any]],
        current_decision: Optional[Dict[str, Any]],
    ) -> CourseBriefResponse:
        """Добавляет уникальные темы блока, дубли откладывает, завершает модуль."""
        module = draft_course.modules[current_index]
        history = self._decision_history(current_decision)
        comment = (answer.comment or "").strip()

        if is_clarifying_question(comment):
            other_topics = collect_other_module_topics(draft_course.modules, module.module_number)
            return self._answer_lesson_clarification(
                record=record,
                answer=answer,
                current_revision=current_revision,
                draft_course=draft_course,
                current_index=current_index,
                decisions=decisions,
                current_decision=current_decision,
                history=history,
                phase=PHASE_LESSON_EXTRAS,
                pending_kind=CourseBriefQuestionKind.LESSON_EXTRAS.value,
                follow_up_question=lesson_extras_question(module.module_title, other_topics),
            )

        requested = parse_extra_topics_from_comment(comment)
        other_topics = collect_other_module_topics(draft_course.modules, module.module_number)
        duplicates = find_duplicate_topics(requested, other_topics)
        duplicate_keys = {
            (item.get("requested") or "").strip().lower() for item in duplicates
        }
        unique_extras = [
            title
            for title in requested
            if title.strip().lower() not in duplicate_keys
        ]

        deferred_topics = list(self._load_json(record.get("deferred_topics"), []) or [])
        if not isinstance(deferred_topics, list):
            deferred_topics = []
        for item in duplicates:
            target_number = item.get("module_number")
            if not isinstance(target_number, int):
                continue
            deferred_topics.append(
                {
                    "module_number": target_number,
                    "title": item.get("existing_title") or item.get("requested"),
                    "from_module_number": module.module_number,
                    "from_module_title": module.module_title,
                    "note": "Тема уже есть в другом блоке; уточните при его разборе.",
                }
            )

        if unique_extras:
            draft_course = self._append_extra_lessons(draft_course, current_index, unique_extras)
            module = draft_course.modules[current_index]
            lesson_decisions = list(current_decision.get("lesson_decisions") or [])
            for title in unique_extras:
                lesson_decisions.append(
                    {
                        "title": title,
                        "include": True,
                        "knowledge_level": current_decision.get("knowledge_level"),
                        "note": "Добавлено на фазе lesson_extras",
                    }
                )
        else:
            lesson_decisions = current_decision.get("lesson_decisions")

        notice = ""
        if duplicates:
            parts = [
                f"«{item.get('requested')}» уже в «{item.get('module_title')}»"
                for item in duplicates
                if item.get("requested")
            ]
            notice = " Не дублирую: " + "; ".join(parts) + "."

        is_last = current_index >= len(draft_course.modules) - 1
        finish_course = bool(is_last)

        return self._persist_lesson_phase_step(
            record=record,
            answer=answer,
            current_revision=current_revision,
            draft_course=draft_course,
            current_index=current_index,
            decisions=decisions,
            current_decision=current_decision,
            history=history,
            phase=PHASE_DONE,
            pending_question=None,
            pending_kind=None,
            lesson_followup_count=0,
            signals_patch=None,
            lesson_decisions=lesson_decisions,
            extra_topics=unique_extras,
            finalize=True,
            deferred_topics=deferred_topics,
            assistant_suffix=notice,
            finish_course=finish_course,
        )

    def _answer_lesson_clarification(
        self,
        *,
        record: Dict[str, Any],
        answer: CourseBriefAnswerRequest,
        current_revision: int,
        draft_course: Course,
        current_index: int,
        decisions: List[Dict[str, Any]],
        current_decision: Optional[Dict[str, Any]],
        history: List[Dict[str, str]],
        phase: str,
        pending_kind: str,
        follow_up_question: str,
    ) -> CourseBriefResponse:
        """Отвечает на уточнение по уроку и фиксирует обещанные детали."""
        module = draft_course.modules[current_index]
        matched = match_lesson_by_comment(answer.comment, module.lessons)
        promises_to_add: List[Dict[str, Any]] = []
        if matched is not None:
            promises_to_add.append(snapshot_lesson_promise(matched))
        else:
            # Если урок не назван явно — фиксируем весь показанный краткий обзор.
            promises_to_add.extend(
                snapshot_lesson_promise(lesson) for lesson in module.lessons[:4]
            )

        pending_question = clarifying_reply_for_lessons(
            answer.comment,
            module.lessons,
            follow_up_question=follow_up_question,
        )
        lesson_followups = int((current_decision or {}).get("lesson_followup_count") or 0)
        return self._persist_lesson_phase_step(
            record=record,
            answer=answer,
            current_revision=current_revision,
            draft_course=draft_course,
            current_index=current_index,
            decisions=decisions,
            current_decision=current_decision,
            history=history,
            phase=phase,
            pending_question=pending_question,
            pending_kind=pending_kind,
            lesson_followup_count=lesson_followups,
            signals_patch=None,
            lesson_decisions=None,
            extra_topics=None,
            finalize=False,
            deferred_topics=None,
            lesson_promises=merge_lesson_promises(
                (current_decision or {}).get("lesson_promises"),
                promises_to_add,
            ),
        )

    def _persist_lesson_phase_step(
        self,
        *,
        record: Dict[str, Any],
        answer: CourseBriefAnswerRequest,
        current_revision: int,
        draft_course: Course,
        current_index: int,
        decisions: List[Dict[str, Any]],
        current_decision: Optional[Dict[str, Any]],
        history: List[Dict[str, str]],
        phase: str,
        pending_question: Optional[str],
        pending_kind: Optional[str],
        lesson_followup_count: int,
        signals_patch: Optional[Dict[str, Any]],
        lesson_decisions: Optional[List[Dict[str, Any]]],
        extra_topics: Optional[List[str]],
        finalize: bool,
        deferred_topics: Optional[List[Dict[str, Any]]],
        assistant_suffix: str = "",
        finish_course: bool = False,
        lesson_promises: Optional[List[Dict[str, Any]]] = None,
    ) -> CourseBriefResponse:
        """Сохраняет шаг фаз lesson_scope / lesson_extras."""
        module = draft_course.modules[current_index]
        session_id = record["id"]
        user_message = self._format_answer_message(answer)
        updated_history = [*history, {"role": "user", "content": user_message}]

        next_index = current_index
        assistant_message = pending_question or ""
        if finalize and not finish_course:
            next_index = current_index + 1
            assistant_message = self._build_question(draft_course, next_index).text
            if assistant_suffix:
                assistant_message = assistant_message + assistant_suffix
        elif finalize and finish_course:
            assistant_message = (
                "Спасибо, уточнения собраны. Финальная структура курса готова."
                + assistant_suffix
            )
        elif pending_question:
            updated_history.append({"role": "assistant", "content": pending_question})
            if assistant_suffix:
                assistant_message = pending_question + assistant_suffix

        signals = signals_patch or (
            current_decision.get("signals") if current_decision else {}
        )
        decision = {
            **(current_decision or {}),
            "module_number": module.module_number,
            "module_title": module.module_title,
            "comment": (answer.comment or "").strip() or (current_decision or {}).get("comment"),
            "signals": signals,
            "history": updated_history,
            "confidence_percentage": confidence_from_signals(signals)[0]
            if isinstance(signals, dict)
            else (current_decision or {}).get("confidence_percentage"),
            "phase": phase,
            "finalized": finalize,
            "pending_question": pending_question if not finalize else None,
            "pending_question_kind": pending_kind if not finalize else None,
            "pending_structure_change": None,
            "lesson_followup_count": lesson_followup_count,
            "lesson_decisions": lesson_decisions
            if lesson_decisions is not None
            else (current_decision or {}).get("lesson_decisions"),
            "extra_topics": extra_topics
            if extra_topics is not None
            else (current_decision or {}).get("extra_topics"),
            "lesson_promises": lesson_promises
            if lesson_promises is not None
            else (current_decision or {}).get("lesson_promises"),
        }
        decisions = self._upsert_decision(decisions, decision)
        revision = current_revision + 1
        updates: Dict[str, Any] = {
            "decisions": decisions,
            "revision": revision,
            "total_questions": len(draft_course.modules),
            "preliminary_outline": self._dump_model(draft_course),
            "current_question_index": next_index if finalize else current_index,
        }
        if deferred_topics is not None:
            updates["deferred_topics"] = deferred_topics
        if finalize and finish_course:
            final_course = self._refine_outline(draft_course, decisions, record["topic"])
            updates.update(
                {
                    "status": CourseBriefStatus.COMPLETED.value,
                    "final_outline": self._dump_model(final_course),
                    "current_question_index": len(draft_course.modules),
                }
            )

        if not self._storage.update_course_brief(
            session_id,
            updates,
            expected_revision=answer.expected_revision,
        ):
            raise CourseBriefInvalidStateError(
                "Сессия уже изменилась. Обновите страницу перед отправкой ответа."
            )
        message_sequence = self._next_message_sequence(session_id)
        self._storage.add_course_brief_message(
            session_id,
            "user",
            user_message,
            message_sequence,
        )
        self._storage.add_course_brief_message(
            session_id,
            "assistant",
            assistant_message,
            message_sequence + 1,
        )
        return self._build_response({**record, **updates})

    @staticmethod
    def _module_phase(decision: Optional[Dict[str, Any]]) -> str:
        if not decision:
            return PHASE_MODULE_GATE
        phase = decision.get("phase")
        if phase in {
            PHASE_MODULE_GATE,
            PHASE_LESSON_SCOPE,
            PHASE_LESSON_EXTRAS,
            PHASE_DONE,
        }:
            return str(phase)
        kind = decision.get("pending_question_kind")
        if kind == CourseBriefQuestionKind.LESSON_SCOPE.value:
            return PHASE_LESSON_SCOPE
        if kind == CourseBriefQuestionKind.LESSON_EXTRAS.value:
            return PHASE_LESSON_EXTRAS
        return PHASE_MODULE_GATE

    @staticmethod
    def _deferred_topics_for_module(
        record: Dict[str, Any],
        module_number: int,
    ) -> List[Dict[str, Any]]:
        raw = record.get("deferred_topics")
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                return []
        if not isinstance(raw, list):
            return []
        return [
            item
            for item in raw
            if isinstance(item, dict) and item.get("module_number") == module_number
        ]

    def _ensure_module_lesson_draft(
        self,
        draft_course: Course,
        module_index: int,
        *,
        topic: str,
        depth: Optional[str],
        knowledge_level: Optional[str],
    ) -> Course:
        """Гарантирует черновик уроков модуля перед фазой lesson_scope."""
        module = draft_course.modules[module_index]
        if module.lessons:
            return draft_course

        other_topics = collect_other_module_topics(draft_course.modules, module.module_number)
        other_text = "\n".join(
            f"- {item['title']} ({item['module_title']})" for item in other_topics[:20]
        ) or "- нет"
        call_kwargs: Dict[str, Any] = {
            "system_prompt": COURSE_BRIEF_LESSON_DRAFT_SYSTEM_PROMPT,
            "user_prompt": COURSE_BRIEF_LESSON_DRAFT_PROMPT_TEMPLATE.format(
                topic=topic,
                module_title=module.module_title,
                module_goal=module.module_goal,
                depth=depth or "standard",
                knowledge_level=knowledge_level or "middle",
                current_lessons="- нет",
                other_topics=other_text,
            ),
            "temperature": 0.3,
            "max_tokens": 1200,
        }
        lessons: List[Lesson] = []
        try:
            raw = self._get_ai_client().call_ai_json(**call_kwargs)
            items = raw.get("lessons") if isinstance(raw, dict) else None
            if isinstance(items, list):
                for item in items[:6]:
                    if not isinstance(item, dict) or not item.get("lesson_title"):
                        continue
                    lessons.append(
                        Lesson(
                            lesson_title=str(item["lesson_title"]).strip(),
                            lesson_goal=str(item.get("lesson_goal") or "Разобрать тему.").strip(),
                            content_outline=item.get("content_outline")
                            if isinstance(item.get("content_outline"), list)
                            else ["Контекст", "Практика"],
                            assessment=str(item.get("assessment") or "Практика"),
                            format=LessonFormat(item["format"])
                            if item.get("format") in {f.value for f in LessonFormat}
                            else LessonFormat.THEORY,
                            estimated_time_minutes=int(item.get("estimated_time_minutes") or 45),
                        )
                    )
        except Exception:
            logger.warning("Не удалось сгенерировать черновик уроков, используем шаблон")

        if not lessons:
            lessons = [
                Lesson(
                    lesson_title=f"Основы: {module.module_title}",
                    lesson_goal="Понять ключевые понятия блока.",
                    content_outline=["Контекст", "Термины", "Пример"],
                    assessment="Короткая практика",
                    format=LessonFormat.THEORY,
                    estimated_time_minutes=30,
                ),
                Lesson(
                    lesson_title=f"Практика: {module.module_title}",
                    lesson_goal="Применить материал блока.",
                    content_outline=["Задание", "Разбор", "Самопроверка"],
                    assessment="Практическое задание",
                    format=LessonFormat.PRACTICE,
                    estimated_time_minutes=45,
                ),
            ]

        modules = list(draft_course.modules)
        updated = self._copy_model(module)
        updated.lessons = lessons
        modules[module_index] = updated
        payload = self._dump_model(draft_course)
        payload["modules"] = [self._dump_model(item) for item in modules]
        return Course(**payload)

    def _append_extra_lessons(
        self,
        draft_course: Course,
        module_index: int,
        titles: List[str],
    ) -> Course:
        """Добавляет уникальные темы как уроки текущего модуля."""
        module = draft_course.modules[module_index]
        existing = {(lesson.lesson_title or "").strip().lower() for lesson in module.lessons}
        lessons = [self._copy_model(lesson) for lesson in module.lessons]
        for title in titles:
            key = title.strip().lower()
            if not key or key in existing:
                continue
            existing.add(key)
            lessons.append(
                Lesson(
                    lesson_title=title.strip(),
                    lesson_goal=f"Разобрать тему «{title.strip()}».",
                    content_outline=["Контекст", "Практика", "Проверка"],
                    assessment="Практика",
                    format=LessonFormat.THEORY,
                    estimated_time_minutes=40,
                )
            )
        modules = list(draft_course.modules)
        updated = self._copy_model(module)
        updated.lessons = lessons
        modules[module_index] = updated
        payload = self._dump_model(draft_course)
        payload["modules"] = [self._dump_model(item) for item in modules]
        return Course(**payload)

    def _interpret_module_answer(
        self,
        *,
        topic: str,
        module: Module,
        total_modules: int,
        completed_modules: int,
        included_modules: int,
        history: List[Dict[str, str]],
        answer: CourseBriefAnswerRequest,
        followup_count: int,
        pending_structure_change: Optional[Dict[str, Any]] = None,
        phase: str = PHASE_MODULE_GATE,
        other_modules_topics: Optional[List[Dict[str, Any]]] = None,
    ) -> tuple[CourseBriefInterviewResult, bool]:
        """Вызывает extractor-модель и возвращает безопасный fallback при сбое."""
        payload = {
            "topic": topic,
            "phase": phase,
            "module": {
                "id": str(module.module_number),
                "title": module.module_title,
                "goal": module.module_goal,
                "lessons": [
                    {"title": lesson.lesson_title}
                    for lesson in module.lessons
                    if lesson.lesson_title
                ],
            },
            "module_count": total_modules,
            "completed_modules": completed_modules,
            "included_modules": included_modules,
            "followup_count": followup_count,
            "max_followups": MAX_MODULE_FOLLOWUPS,
            "pending_structure_change": pending_structure_change or {"kind": "none"},
            "other_modules_topics": other_modules_topics or [],
            "history": history,
            "answer": {
                "depth": answer.depth.value if answer.depth is not None else None,
                "knowledge_level": (
                    answer.knowledge_level.value if answer.knowledge_level is not None else None
                ),
                "comment": (answer.comment or "").strip(),
            },
        }
        call_kwargs: Dict[str, Any] = {
            "system_prompt": COURSE_BRIEF_INTERVIEW_SYSTEM_PROMPT,
            "user_prompt": COURSE_BRIEF_INTERVIEW_PROMPT_TEMPLATE.format(
                payload=json.dumps(payload, ensure_ascii=False),
            ),
            "temperature": 0.2,
            "max_tokens": 1200,
            "retries": 1,
            "backoff_seconds": 0.5,
            "json_schema": course_brief_interview_json_schema(),
        }
        try:
            from backend.config import settings

            call_kwargs.update(
                {
                    "model": getattr(
                        settings,
                        "COURSE_BRIEF_INTERVIEW_MODEL",
                        settings.OPENAI_MODEL_DEFAULT,
                    ),
                    "temperature": getattr(settings, "COURSE_BRIEF_INTERVIEW_TEMPERATURE", 0.2),
                    "max_tokens": getattr(settings, "COURSE_BRIEF_INTERVIEW_MAX_TOKENS", 1200),
                    "retries": settings.OPENAI_RETRIES_DEFAULT,
                    "backoff_seconds": settings.OPENAI_BACKOFF_SECONDS_DEFAULT,
                }
            )
        except ModuleNotFoundError:
            # Изолированные unit-тесты подставляют AI-клиент без settings.
            pass

        try:
            client = self._get_ai_client()
            try:
                raw_result = client.call_ai_json(**call_kwargs)
            except TypeError as error:
                # Поддержка старого клиентского порта, пока он не получил
                # параметр json_schema. JSON-валидация ниже остаётся строгой.
                if "json_schema" not in str(error):
                    raise
                call_kwargs.pop("json_schema", None)
                raw_result = client.call_ai_json(**call_kwargs)
            if raw_result is not None:
                return validate_interview_result(raw_result, answer, history), False
            logger.info("Интервью-модель не вернула JSON; используем local fallback")
        except Exception as error:
            logger.warning("Некорректный ответ интервью-модели: %s", error)

        return make_fallback_result(answer), True

    @staticmethod
    def _select_follow_up_question(
        result: CourseBriefInterviewResult,
        signals: Any,
        kind: CourseBriefQuestionKind,
        lesson_titles: Optional[List[str]] = None,
        comment: Optional[str] = None,
    ) -> str:
        if kind == CourseBriefQuestionKind.REVISE_GOAL:
            if result.action == CourseBriefInterviewAction.REVISE_GOAL and result.follow_up_question:
                return result.follow_up_question.strip()
            return CourseBriefService._fallback_revise_goal_question()

        gap = primary_missing_signal(signals, MODULE_GATE_SIGNALS)
        requested_topics = extract_requested_topics(comment, lesson_titles)
        # Scope-вопрос без списка уроков бесполезен: пользователь не видит черновик.
        if gap == "scope":
            return scope_question_for_lessons(lesson_titles, requested_topics)

        if result.action == CourseBriefInterviewAction.ASK and result.follow_up_question:
            question = result.follow_up_question.strip()
            if is_vague_topic_question(question, lesson_titles):
                return scope_question_for_lessons(lesson_titles, requested_topics)
            return question

        return default_question_for_missing(signals, lesson_titles)

    @staticmethod
    def _select_add_module_question(
        result: CourseBriefInterviewResult,
        structure_request: Any,
    ) -> str:
        if (
            result.structure_request.kind == CourseBriefStructureChangeKind.ADD_MODULE
            and result.follow_up_question
        ):
            return result.follow_up_question.strip()
        return add_module_question(structure_request)

    @staticmethod
    def _fallback_revise_goal_question() -> str:
        return "Все предложенные разделы исключены. Какую основную цель вы хотите достичь с помощью курса?"

    def _restart_after_revised_goal(
        self,
        *,
        record: Dict[str, Any],
        answer: CourseBriefAnswerRequest,
        current_revision: int,
    ) -> CourseBriefResponse:
        """Строит новый скрытый draft по уточнённой цели в той же сессии."""
        revised_goal = (answer.comment or "").strip()
        if not revised_goal:
            raise CourseBriefInvalidStateError("Опишите новую цель курса текстом.")

        draft_course = self._generate_draft_course(record["topic"], revised_goal)
        updates: Dict[str, Any] = {
            "status": CourseBriefStatus.QUESTIONING.value,
            "preliminary_outline": self._dump_model(draft_course),
            "decisions": [],
            "current_question_index": 0,
            "total_questions": len(draft_course.modules),
            "final_outline": None,
            "revision": current_revision + 1,
        }
        if not self._storage.update_course_brief(
            record["id"],
            updates,
            expected_revision=answer.expected_revision,
        ):
            raise CourseBriefInvalidStateError(
                "Сессия уже изменилась. Обновите страницу перед отправкой ответа."
            )

        message_sequence = self._next_message_sequence(record["id"])
        self._storage.add_course_brief_message(
            record["id"],
            "user",
            revised_goal,
            message_sequence,
        )
        self._storage.add_course_brief_message(
            record["id"],
            "assistant",
            self._build_question(draft_course, 0).text,
            message_sequence + 1,
        )
        return self._build_response({**record, **updates})

    def _generate_draft_course(self, topic: str, course_goals: str) -> Course:
        """Создаёт и проверяет новый скрытый черновик для старта или revise_goal."""
        try:
            draft_data = self._get_ai_client().generate_course_structure(
                topic=topic,
                audience_level=self.DEFAULT_AUDIENCE_LEVEL,
                module_count=self.DEFAULT_MODULE_COUNT,
                course_goals=course_goals,
                duration_weeks=self.DEFAULT_DURATION_WEEKS,
                hours_per_week=self.DEFAULT_HOURS_PER_WEEK,
            )
        except Exception as error:
            logger.exception("Не удалось сформировать черновик структуры курса")
            raise CourseBriefGenerationError("Не удалось сформировать черновик структуры курса") from error
        if not draft_data:
            raise CourseBriefGenerationError("Модель не вернула черновик структуры курса")
        try:
            draft_course = Course(**draft_data)
        except Exception as error:
            logger.exception("Модель вернула некорректный черновик структуры курса")
            raise CourseBriefGenerationError("Модель вернула некорректную структуру курса") from error
        if not draft_course.modules:
            raise CourseBriefGenerationError("В черновике структуры нет разделов для уточнения")
        return draft_course

    @staticmethod
    def _decision_for_module(
        decisions: List[Dict[str, Any]],
        module_number: int,
    ) -> Optional[Dict[str, Any]]:
        for decision in reversed(decisions):
            if decision.get("module_number") == module_number:
                return decision
        return None

    @staticmethod
    def _upsert_decision(
        decisions: List[Dict[str, Any]],
        replacement: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        updated = list(decisions)
        for index, decision in enumerate(updated):
            if decision.get("module_number") == replacement["module_number"]:
                updated[index] = replacement
                return updated
        updated.append(replacement)
        return updated

    @staticmethod
    def _decision_history(decision: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
        history = decision.get("history") if decision else []
        if not isinstance(history, list):
            return []
        return [
            {"role": item["role"], "content": item["content"]}
            for item in history
            if isinstance(item, dict)
            and item.get("role") in {"user", "assistant"}
            and isinstance(item.get("content"), str)
        ]

    @staticmethod
    def _followup_count(decision: Optional[Dict[str, Any]]) -> int:
        if not decision:
            return 0
        try:
            return max(0, min(int(decision.get("followup_count") or 0), MAX_MODULE_FOLLOWUPS))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _structure_followup_count(pending_change: Optional[Dict[str, Any]]) -> int:
        if not isinstance(pending_change, dict):
            return 0
        try:
            return max(0, min(int(pending_change.get("followup_count") or 0), MAX_ADD_MODULE_FOLLOWUPS))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _shift_decisions_after_insert(
        decisions: List[Dict[str, Any]],
        inserted_number: int,
    ) -> List[Dict[str, Any]]:
        """Сдвигает номера решений после вставки модуля в середину черновика."""
        updated: List[Dict[str, Any]] = []
        for decision in decisions:
            item = dict(decision)
            number = item.get("module_number")
            if isinstance(number, int) and number >= inserted_number:
                item["module_number"] = number + 1
            updated.append(item)
        return updated

    def _insert_requested_module(
        self,
        draft_course: Course,
        current_index: int,
        structure_request: Any,
        topic: str,
    ) -> Course:
        """Вставляет запрошенный раздел сразу после текущего и перенумеровывает черновик."""
        title = (getattr(structure_request, "title", None) or "").strip() or "Новый раздел"
        purpose = (getattr(structure_request, "purpose", None) or "").strip() or (
            f"Изучить тему «{title}» в курсе «{topic}»."
        )
        new_module = Module(
            module_number=current_index + 2,
            module_title=title[:120],
            module_goal=purpose[:500],
            lessons=[
                Lesson(
                    lesson_title=f"Основы: {title}",
                    lesson_goal=purpose,
                    content_outline=["Контекст", "Ключевые понятия", "Пример"],
                    assessment="Короткая практика",
                    format=LessonFormat.THEORY,
                    estimated_time_minutes=30,
                ),
                Lesson(
                    lesson_title=f"Практика: {title}",
                    lesson_goal="Применить материал раздела в рабочем сценарии.",
                    content_outline=["Задание", "Разбор", "Самопроверка"],
                    assessment="Практическое задание",
                    format=LessonFormat.PRACTICE,
                    estimated_time_minutes=45,
                ),
            ],
        )
        modules = list(draft_course.modules)
        modules.insert(current_index + 1, new_module)
        for index, item in enumerate(modules, start=1):
            item.module_number = index
        payload = self._dump_model(draft_course)
        payload["modules"] = [self._dump_model(item) for item in modules]
        logger.info("✅ В черновик добавлен раздел «%s», вопросов: %s", title, len(modules))
        return Course(**payload)

    @staticmethod
    def _pending_question_kind(decision: Optional[Dict[str, Any]]) -> Optional[str]:
        if not decision:
            return None
        value = decision.get("pending_question_kind")
        return value if isinstance(value, str) else None

    @staticmethod
    def _completed_modules(decisions: List[Dict[str, Any]], current_module_number: int) -> int:
        return sum(
            1
            for decision in decisions
            if decision.get("module_number") != current_module_number
            and decision.get("finalized", True)
        )

    @staticmethod
    def _included_modules(decisions: List[Dict[str, Any]], current_module_number: int) -> int:
        count = 0
        for decision in decisions:
            if decision.get("module_number") == current_module_number or not decision.get("finalized", True):
                continue
            signals = decision.get("signals") or {}
            necessity = signals.get("necessity") if isinstance(signals, dict) else None
            if isinstance(necessity, dict) and necessity.get("status") == "confirmed":
                if necessity.get("value") == "include":
                    count += 1
            elif decision.get("depth") not in {None, CourseBriefDepth.SKIP.value}:
                # Совместимость с решениями, сохранёнными до появления signals.
                count += 1
        return count

    @staticmethod
    def _decision_depth(signals: Any, answer: CourseBriefAnswerRequest) -> Optional[str]:
        necessity = signals.necessity
        if (
            necessity.status == CourseBriefSignalStatus.CONFIRMED
            and necessity.value == "exclude"
        ):
            return CourseBriefDepth.SKIP.value
        if signals.depth.status == CourseBriefSignalStatus.CONFIRMED:
            return signals.depth.value
        return answer.depth.value if answer.depth is not None else None

    @staticmethod
    def _decision_knowledge_level(signals: Any, answer: CourseBriefAnswerRequest) -> Optional[str]:
        if signals.knowledge.status == CourseBriefSignalStatus.CONFIRMED:
            return signals.knowledge.value
        return answer.knowledge_level.value if answer.knowledge_level is not None else None

    def _next_message_sequence(self, session_id: str) -> int:
        """Выделяет новый sequence, поэтому follow-up не конфликтует с предыдущими."""
        try:
            messages = self._storage.get_course_brief_messages(session_id)
        except Exception:
            logger.warning("Не удалось прочитать историю сообщений для sequence", exc_info=True)
            return 1
        values = [
            item.get("sequence")
            for item in messages
            if isinstance(item, dict) and isinstance(item.get("sequence"), int)
        ]
        return (max(values) + 1) if values else 1

    def _get_ai_client(self) -> Any:
        """Создаёт AI-клиент только в момент первого обращения к модели."""
        if self._ai_client is None:
            from backend.config import settings

            if settings.COURSE_BRIEF_DEMO_MODE:
                from backend.ai.course_brief_demo_client import CourseBriefDemoClient

                self._ai_client = CourseBriefDemoClient()
                return self._ai_client

            from backend.ai.openai_client import OpenAIClient

            self._ai_client = OpenAIClient()
        return self._ai_client

    def _get_record(self, session_id: str) -> Dict[str, Any]:
        record = self._storage.get_course_brief(session_id)
        if not record:
            raise CourseBriefNotFoundError("Сессия уточнения не найдена")
        return record

    def _build_response(self, record: Dict[str, Any]) -> CourseBriefResponse:
        """Формирует API-ответ, намеренно исключая предварительную структуру."""
        status = CourseBriefStatus(record["status"])
        total_questions = int(record.get("total_questions") or 0)
        current_index = int(record.get("current_question_index") or 0)
        completed_questions = min(current_index, total_questions)
        percentage = round(completed_questions * 100 / total_questions) if total_questions else 100
        progress = CourseBriefProgress(
            completed_questions=completed_questions,
            total_questions=total_questions,
            percentage=percentage,
            remaining_questions=max(total_questions - completed_questions, 0),
        )

        question = None
        final_course = None
        decisions = self._load_json(record.get("decisions"), [])
        if not isinstance(decisions, list):
            decisions = []
        draft_course = None
        if status == CourseBriefStatus.QUESTIONING:
            draft_course = Course(**self._load_json(record.get("preliminary_outline"), {}))
            if current_index >= len(draft_course.modules):
                raise CourseBriefInvalidStateError("В интервью больше нет вопросов")
            current_module = draft_course.modules[current_index]
            decision = self._decision_for_module(decisions, current_module.module_number)
            pending_text = decision.get("pending_question") if decision else None
            pending_kind = self._pending_question_kind(decision)
            if isinstance(pending_text, str) and pending_text.strip() and pending_kind:
                try:
                    kind = CourseBriefQuestionKind(pending_kind)
                except ValueError:
                    kind = CourseBriefQuestionKind.FOLLOW_UP
                question = self._build_question(
                    draft_course,
                    current_index,
                    text=pending_text.strip(),
                    kind=kind,
                    answer_controls=self._answer_controls_for_decision(decision, kind),
                )
            else:
                question = self._build_question(draft_course, current_index)
        elif record.get("final_outline"):
            final_course = Course(**self._load_json(record["final_outline"], {}))

        confidence = self._build_confidence(
            decisions=decisions,
            total_questions=total_questions,
            current_index=current_index,
            status=status,
            draft_course=draft_course,
        )

        return CourseBriefResponse(
            session_id=record["id"],
            topic=record["topic"],
            status=status,
            revision=int(record.get("revision") or 1),
            progress=progress,
            confidence=confidence,
            question=question,
            final_course=final_course,
            messages=self._load_chat_messages(record["id"]),
        )

    def _load_chat_messages(self, session_id: str) -> List[CourseBriefChatMessage]:
        """Читает историю диалога для безопасного восстановления UI."""
        try:
            raw_messages = self._storage.get_course_brief_messages(session_id)
        except Exception:
            logger.warning("Не удалось прочитать историю сообщений интервью", exc_info=True)
            return []
        result: List[CourseBriefChatMessage] = []
        for item in raw_messages or []:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = item.get("content")
            sequence = item.get("sequence")
            if role not in {"user", "assistant"} or not isinstance(content, str):
                continue
            try:
                sequence_number = int(sequence or len(result) + 1)
            except (TypeError, ValueError):
                sequence_number = len(result) + 1
            result.append(
                CourseBriefChatMessage(
                    role=role,
                    content=content,
                    sequence=max(1, sequence_number),
                )
            )
        return result

    @staticmethod
    def _answer_controls_for_decision(
        decision: Optional[Dict[str, Any]],
        kind: CourseBriefQuestionKind,
    ) -> CourseBriefAnswerControls:
        """Подбирает UI ответа под тип уточнения."""
        if kind == CourseBriefQuestionKind.MODULE:
            return CourseBriefAnswerControls.MODULE_GATE
        if kind in {
            CourseBriefQuestionKind.REVISE_GOAL,
            CourseBriefQuestionKind.ADD_MODULE,
            CourseBriefQuestionKind.SPLIT_MODULE,
            CourseBriefQuestionKind.LESSON_SCOPE,
            CourseBriefQuestionKind.LESSON_EXTRAS,
        }:
            return CourseBriefAnswerControls.TEXT
        stored = decision.get("pending_answer_controls") if decision else None
        if stored in {item.value for item in CourseBriefAnswerControls}:
            return CourseBriefAnswerControls(stored)
        signals_payload = decision.get("signals") if decision else None
        try:
            from backend.services.course_brief_interview import CourseBriefInterviewSignals

            signals = CourseBriefInterviewSignals.model_validate(signals_payload or {})
            gap = primary_missing_signal(signals, MODULE_GATE_SIGNALS)
        except Exception:
            gap = None
        if gap == "knowledge":
            return CourseBriefAnswerControls.KNOWLEDGE
        if gap == "depth" or gap == "necessity":
            return CourseBriefAnswerControls.DEPTH
        return CourseBriefAnswerControls.TEXT

    @staticmethod
    def _build_question(
        draft_course: Course,
        question_index: int,
        *,
        text: Optional[str] = None,
        kind: CourseBriefQuestionKind = CourseBriefQuestionKind.MODULE,
        answer_controls: Optional[CourseBriefAnswerControls] = None,
    ) -> CourseBriefQuestion:
        """Создаёт вопрос только о текущем разделе, не показывая весь outline."""
        module = draft_course.modules[question_index]
        controls = answer_controls
        if controls is None:
            controls = (
                CourseBriefAnswerControls.MODULE_GATE
                if kind == CourseBriefQuestionKind.MODULE
                else CourseBriefAnswerControls.TEXT
            )
        return CourseBriefQuestion(
            number=question_index + 1,
            total=len(draft_course.modules),
            text=text or (
                f"В будущем курсе предусмотрен блок «{module.module_title}». "
                "Насколько он нужен, как глубоко его разобрать и какой у вас текущий уровень?"
            ),
            kind=kind,
            answer_controls=controls,
        )

    def _build_confidence(
        self,
        *,
        decisions: List[Dict[str, Any]],
        total_questions: int,
        current_index: int,
        status: CourseBriefStatus,
        draft_course: Optional[Course],
    ) -> CourseBriefConfidence:
        """Считает полноту решений независимо от прогресса по модулям."""
        total = max(total_questions, 1)
        decision_scores = {
            decision.get("module_number"): confidence_from_signals(decision.get("signals"))[0]
            for decision in decisions
            if isinstance(decision, dict)
        }
        structure_percentage = round(sum(decision_scores.values()) * 100 / (total * 100))

        current_decision: Optional[Dict[str, Any]] = None
        if draft_course is not None and current_index < len(draft_course.modules):
            current_decision = self._decision_for_module(
                decisions,
                draft_course.modules[current_index].module_number,
            )
        elif status == CourseBriefStatus.COMPLETED and decisions:
            current_decision = decisions[-1]

        current_percentage, confirmed_signals = confidence_from_signals(
            current_decision.get("signals") if current_decision else None
        )
        if current_percentage >= 85:
            current_status = "high"
        elif current_percentage >= 60:
            current_status = "medium"
        else:
            current_status = "low"
        return CourseBriefConfidence(
            current_module_percentage=current_percentage,
            structure_percentage=structure_percentage,
            current_module_status=current_status,
            confirmed_signals=confirmed_signals,
        )

    def _refine_outline(
        self,
        draft_course: Course,
        decisions: List[Dict[str, Any]],
        topic: str,
    ) -> Course:
        """Просит AI собрать финальный outline; при сбое применяет решения детерминированно."""
        base_course = self._apply_decisions(draft_course, decisions)
        try:
            ai_call_kwargs: Dict[str, Any] = {
                "system_prompt": COURSE_BRIEF_REFINEMENT_SYSTEM_PROMPT,
                "user_prompt": COURSE_BRIEF_REFINEMENT_PROMPT_TEMPLATE.format(
                    topic=topic,
                    draft_structure=json.dumps(self._dump_model(base_course), ensure_ascii=False),
                    decisions=json.dumps(decisions, ensure_ascii=False),
                ),
                "temperature": 0.4,
            }
            try:
                from backend.config import settings

                ai_call_kwargs.update(
                    {
                        "model": settings.OPENAI_MODEL_DEFAULT,
                        "max_tokens": settings.OPENAI_MAX_TOKENS_COURSE_STRUCTURE,
                        "retries": settings.OPENAI_RETRIES_DEFAULT,
                        "backoff_seconds": settings.OPENAI_BACKOFF_SECONDS_DEFAULT,
                    }
                )
            except ModuleNotFoundError:
                # В изолированных тестах можно подставить AI-клиент без пакетов окружения.
                pass

            refined_data = self._get_ai_client().call_ai_json(**ai_call_kwargs)
            if refined_data:
                refined = self._validate_refined_outline(refined_data, base_course)
                return self._reapply_lesson_promises_to_course(refined, decisions)
            logger.warning("AI не вернул финальную структуру, применяем безопасный fallback")
        except Exception:
            logger.exception("Не удалось уточнить финальную структуру с помощью AI")

        return base_course

    def _validate_refined_outline(
        self,
        refined_data: Dict[str, Any],
        base_course: Course,
    ) -> Course:
        """Проверяет AI-ответ и сохраняет состав разрешённых модулей неизменным."""
        modules = refined_data.get("modules")
        if not isinstance(modules, list) or len(modules) != len(base_course.modules):
            raise ValueError("Количество модулей не совпадает с решениями пользователя")

        normalized = dict(refined_data)
        normalized["target_audience"] = base_course.target_audience
        for expected_module, module in zip(base_course.modules, modules):
            if not isinstance(module, dict):
                raise ValueError("Модель вернула модуль в неверном формате")
            # Состав и идентичность модулей фиксирует пользовательское решение.
            # Модель может обогатить цели и уроки, но не вернуть пропущенный раздел.
            module["module_number"] = expected_module.module_number
            module["module_title"] = expected_module.module_title

        return Course(**normalized)

    def _reapply_lesson_promises_to_course(
        self,
        course: Course,
        decisions: List[Dict[str, Any]],
    ) -> Course:
        """После refinement возвращает обещанные goal/outline в уроки."""
        by_number = {
            decision.get("module_number"): decision
            for decision in decisions
            if isinstance(decision, dict)
        }
        modules: List[Module] = []
        for module in course.modules:
            decision = by_number.get(module.module_number)
            # После перенумерации ищем также по title.
            if decision is None:
                for item in decisions:
                    if (
                        isinstance(item, dict)
                        and item.get("module_title") == module.module_title
                    ):
                        decision = item
                        break
            updated = self._copy_model(module)
            promises = decision.get("lesson_promises") if isinstance(decision, dict) else None
            updated.lessons = self._apply_lesson_promises(list(updated.lessons), promises)
            modules.append(updated)
        payload = self._dump_model(course)
        payload["modules"] = [self._dump_model(module) for module in modules]
        return Course(**payload)

    @staticmethod
    def _apply_lesson_promises(
        lessons: List[Lesson],
        promises: Optional[Any],
    ) -> List[Lesson]:
        """Накладывает зафиксированные в уточнении goal и outline на уроки."""
        if not isinstance(promises, list) or not promises:
            return lessons
        by_title = {
            str(item.get("title") or "").strip().lower(): item
            for item in promises
            if isinstance(item, dict) and str(item.get("title") or "").strip()
        }
        if not by_title:
            return lessons
        applied: List[Lesson] = []
        for lesson in lessons:
            key = (lesson.lesson_title or "").strip().lower()
            promise = by_title.get(key)
            if not promise:
                applied.append(lesson)
                continue
            updated = lesson.model_copy(deep=True) if hasattr(lesson, "model_copy") else lesson
            if hasattr(lesson, "model_copy"):
                goal = promise.get("promised_goal")
                outline = promise.get("promised_outline")
                if isinstance(goal, str) and goal.strip():
                    updated.lesson_goal = goal.strip()
                if isinstance(outline, list) and outline:
                    updated.content_outline = [str(item).strip() for item in outline if str(item).strip()]
                applied.append(updated)
            else:
                applied.append(lesson)
        return applied

    def _apply_decisions(
        self,
        draft_course: Course,
        decisions: List[Dict[str, Any]],
    ) -> Course:
        """Строит финальную структуру только по финализированным решениям."""
        modules: List[Module] = []
        final_decisions = {
            decision.get("module_number"): decision
            for decision in decisions
            if isinstance(decision, dict) and decision.get("finalized", True)
        }
        for module in draft_course.modules:
            decision = final_decisions.get(module.module_number)
            if not decision:
                # Не добавляем раздел, для которого не было завершённого
                # решения: он не должен появляться в готовом курсе по умолчанию.
                continue
            depth = self._final_decision_depth(decision)
            if depth == CourseBriefDepth.SKIP:
                continue

            refined_module = self._copy_model(module)
            refined_module.module_number = len(modules) + 1
            lessons = [self._copy_model(lesson) for lesson in refined_module.lessons]
            lesson_decisions = decision.get("lesson_decisions")
            if isinstance(lesson_decisions, list) and lesson_decisions:
                include_map = {
                    str(item.get("title") or "").strip().lower(): bool(item.get("include", True))
                    for item in lesson_decisions
                    if isinstance(item, dict)
                }
                if include_map:
                    lessons = [
                        lesson
                        for lesson in lessons
                        if include_map.get((lesson.lesson_title or "").strip().lower(), True)
                    ]
            signals = decision.get("signals") if isinstance(decision.get("signals"), dict) else {}
            scope = signals.get("scope") if isinstance(signals, dict) else None
            if (
                isinstance(scope, dict)
                and scope.get("status") == "confirmed"
                and scope.get("value") == "partial"
            ):
                comment = (decision.get("comment") or "").strip()
                if comment:
                    refined_module.module_goal = (
                        f"{refined_module.module_goal} Нужны только выбранные темы: {comment}"
                    )
            if depth == CourseBriefDepth.BRIEF:
                # Обещанные уроки не выкидываем при сжатии brief.
                promises = decision.get("lesson_promises") if isinstance(
                    decision.get("lesson_promises"), list
                ) else []
                promised_titles = {
                    str(item.get("title") or "").strip().lower()
                    for item in promises
                    if isinstance(item, dict) and item.get("title")
                }
                if promised_titles:
                    kept = [
                        lesson
                        for lesson in lessons
                        if (lesson.lesson_title or "").strip().lower() in promised_titles
                    ]
                    extras = [
                        lesson
                        for lesson in lessons
                        if (lesson.lesson_title or "").strip().lower() not in promised_titles
                    ]
                    lessons = (kept + extras)[: max(2, len(kept))]
                else:
                    lessons = lessons[:2]
                for lesson in lessons:
                    lesson.estimated_time_minutes = max(15, min(lesson.estimated_time_minutes, 30))
            elif depth == CourseBriefDepth.DEEP:
                for lesson in lessons:
                    lesson.estimated_time_minutes = min(480, max(lesson.estimated_time_minutes, 60))
                if not any(
                    getattr(lesson.format, "value", lesson.format) == LessonFormat.PRACTICE.value
                    for lesson in lessons
                ):
                    lessons.append(
                        Lesson(
                            lesson_title=f"Практика: {refined_module.module_title}",
                            lesson_goal="Закрепить материал на прикладном кейсе.",
                            content_outline=["Разбор кейса", "Самостоятельное выполнение", "Обратная связь"],
                            assessment="Практическое задание",
                            format=LessonFormat.PRACTICE,
                            estimated_time_minutes=90,
                        )
                    )
            lessons = self._apply_lesson_promises(lessons, decision.get("lesson_promises"))
            refined_module.lessons = lessons
            modules.append(refined_module)

        payload = self._dump_model(draft_course)
        payload["modules"] = [self._dump_model(module) for module in modules]
        payload["target_audience"] = self._infer_audience(decisions).value
        total_minutes = sum(
            lesson.estimated_time_minutes
            for module in modules
            for lesson in module.lessons
        )
        payload["duration_hours"] = math.ceil(total_minutes / 60) if total_minutes else None
        return Course(**payload)

    @staticmethod
    def _final_decision_depth(decision: Dict[str, Any]) -> CourseBriefDepth:
        """Выбирает безопасную глубину для уже завершённого модуля.

        При явном include без названной глубины используем standard только для
        построения outline; исходный сигнал остаётся missing и понижает
        confidence, поэтому значение не выдаётся за подтверждённый ответ.
        """
        signals = decision.get("signals") if isinstance(decision.get("signals"), dict) else {}
        necessity = signals.get("necessity") if isinstance(signals, dict) else None
        if isinstance(necessity, dict) and necessity.get("status") == "confirmed":
            if necessity.get("value") == "exclude":
                return CourseBriefDepth.SKIP
        raw_depth = decision.get("depth")
        if raw_depth in {depth.value for depth in CourseBriefDepth}:
            return CourseBriefDepth(raw_depth)
        depth_signal = signals.get("depth") if isinstance(signals, dict) else None
        if (
            isinstance(depth_signal, dict)
            and depth_signal.get("status") == "confirmed"
            and depth_signal.get("value") in {
                CourseBriefDepth.BRIEF.value,
                CourseBriefDepth.STANDARD.value,
                CourseBriefDepth.DEEP.value,
            }
        ):
            return CourseBriefDepth(depth_signal["value"])
        if isinstance(necessity, dict) and necessity.get("value") == "include":
            return CourseBriefDepth.STANDARD
        return CourseBriefDepth.SKIP

    @staticmethod
    def _infer_audience(decisions: List[Dict[str, Any]]) -> DifficultyLevel:
        """Выбирает наиболее частый заявленный уровень, а при равенстве — более базовый."""
        order = [DifficultyLevel.JUNIOR, DifficultyLevel.MIDDLE, DifficultyLevel.SENIOR]
        counts = {level: 0 for level in order}
        for decision in decisions:
            value = decision.get("knowledge_level")
            if value in {level.value for level in order}:
                counts[DifficultyLevel(value)] += 1
        return max(order, key=lambda level: (counts[level], -order.index(level)))

    @staticmethod
    def _format_answer_message(answer: CourseBriefAnswerRequest) -> str:
        """Формирует читаемую запись структурированного ответа для истории диалога."""
        depth_labels = {
            CourseBriefDepth.SKIP: "Не нужен",
            CourseBriefDepth.BRIEF: "Кратко",
            CourseBriefDepth.STANDARD: "В рабочем объёме",
            CourseBriefDepth.DEEP: "Глубоко",
        }
        level_labels = {
            DifficultyLevel.JUNIOR: "Начальный уровень",
            DifficultyLevel.MIDDLE: "Есть практика",
            DifficultyLevel.SENIOR: "Продвинутый уровень",
        }
        parts: List[str] = []
        if answer.depth is not None:
            parts.append(depth_labels[answer.depth])
        if answer.knowledge_level:
            parts.append(level_labels[answer.knowledge_level])
        if answer.comment and answer.comment.strip():
            parts.append(answer.comment.strip())
        return " · ".join(parts) or "Текстовое уточнение"

    @staticmethod
    def _dump_model(model: Any) -> Dict[str, Any]:
        """Сериализует Pydantic-модель в JSON-совместимый словарь."""
        if hasattr(model, "model_dump"):
            return model.model_dump(mode="json")
        return model.dict()

    @staticmethod
    def _copy_model(model: Any) -> Any:
        """Создаёт глубокую копию Pydantic-модели для fallback-структуры."""
        if hasattr(model, "model_copy"):
            return model.model_copy(deep=True)
        return model.copy(deep=True)

    @staticmethod
    def _load_json(value: Any, default: Any) -> Any:
        """Принимает JSON из SQLite/PostgreSQL и нормализует его в Python-объект."""
        if value is None:
            return default
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return default
        return value


course_brief_service = CourseBriefService()
