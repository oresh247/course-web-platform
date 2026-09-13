"""Детерминированные правила и схема AI-шага интервью Course Brief.

Модель только извлекает признаки из ответа. Решение о переходе, лимите
уточнений и проценте полноты принимает сервер, поэтому ответ модели нельзя
использовать как исполняемую инструкцию.
"""
from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from backend.models.domain import CourseBriefAnswerRequest, CourseBriefDepth


class CourseBriefSignalStatus(str, Enum):
    """Состояние одного подтверждаемого признака."""

    CONFIRMED = "confirmed"
    MISSING = "missing"
    CONFLICT = "conflict"
    NOT_APPLICABLE = "not_applicable"


class CourseBriefInterviewAction(str, Enum):
    """Допустимые действия, которые может предложить модель."""

    ASK = "ask"
    NEXT_MODULE = "next_module"
    FINISH = "finish"
    REVISE_GOAL = "revise_goal"


class CourseBriefInterviewSignal(BaseModel):
    """Один сигнал модели; семантика проверяется функцией ниже."""

    model_config = ConfigDict(extra="forbid")

    status: CourseBriefSignalStatus
    value: Optional[str] = None
    evidence: List[str] = Field(default_factory=list, max_length=4)


class CourseBriefInterviewSignals(BaseModel):
    """Все обязательные признаки текущего модуля."""

    model_config = ConfigDict(extra="forbid")

    necessity: CourseBriefInterviewSignal
    depth: CourseBriefInterviewSignal
    knowledge: CourseBriefInterviewSignal
    application: CourseBriefInterviewSignal
    scope: CourseBriefInterviewSignal = Field(
        default_factory=lambda: CourseBriefInterviewSignal(
            status=CourseBriefSignalStatus.MISSING
        )
    )


class CourseBriefStructureChangeKind(str, Enum):
    """Запрос на изменение состава черновика, извлечённый из слов пользователя."""

    NONE = "none"
    ADD_MODULE = "add_module"
    SPLIT_MODULE = "split_module"


class CourseBriefStructureRequest(BaseModel):
    """Намерение изменить состав разделов. Решение о применении принимает сервер."""

    model_config = ConfigDict(extra="forbid")

    kind: CourseBriefStructureChangeKind = CourseBriefStructureChangeKind.NONE
    title: Optional[str] = Field(
        default=None,
        max_length=120,
        description="Для add_module — название нового раздела; для split_module — первый блок",
    )
    purpose: Optional[str] = Field(
        default=None,
        max_length=300,
        description="Для add_module — зачем раздел; для split не обязателен",
    )
    second_title: Optional[str] = Field(
        default=None,
        max_length=120,
        description="Для split_module — название второго блока после разделения",
    )
    ready: bool = False
    evidence: List[str] = Field(default_factory=list, max_length=4)


class CourseBriefInterviewResult(BaseModel):
    """Строгий контракт результата извлечения, возвращаемого моделью."""

    model_config = ConfigDict(extra="forbid")

    signals: CourseBriefInterviewSignals
    action: CourseBriefInterviewAction
    follow_up_question: Optional[str] = Field(default=None, max_length=300)
    structure_request: CourseBriefStructureRequest = Field(
        default_factory=CourseBriefStructureRequest
    )


SIGNAL_VALUES = {
    "necessity": {"include", "exclude"},
    "depth": {"brief", "standard", "deep"},
    "knowledge": {"junior", "middle", "senior"},
    "application": {"concrete"},
    "scope": {"whole", "partial"},
}
SIGNAL_WEIGHTS = {
    "necessity": 30,
    "depth": 20,
    "knowledge": 20,
    "scope": 20,
    "application": 10,
}
CRITICAL_SIGNALS = ("necessity", "depth", "knowledge", "scope")
# На фазе module_gate scope ещё не спрашиваем: сначала нужен ли блок и глубина.
MODULE_GATE_SIGNALS = ("necessity", "depth", "knowledge")
MAX_MODULE_FOLLOWUPS = 4
MAX_ADD_MODULE_FOLLOWUPS = 2
MAX_SPLIT_MODULE_FOLLOWUPS = 2
MAX_LESSON_PHASE_FOLLOWUPS = 2
PHASE_MODULE_GATE = "module_gate"
PHASE_LESSON_SCOPE = "lesson_scope"
PHASE_LESSON_EXTRAS = "lesson_extras"
PHASE_DONE = "done"
_ADD_MODULE_PATTERN = re.compile(
    r"(?:добав\w*|нужен|нужно)\s+(?:ещё\s+|еще\s+)?(?:модуль|раздел)\s*"
    r"(?:про|о|:)?\s*(.*)$",
    re.IGNORECASE,
)
_SPLIT_MODULE_PATTERN = re.compile(
    r"(?:раздел\w*|раздели\w*|разбить|разбей|отдел\w+)\s+"
    r"(?:(?:блок|модуль|раздел)\w*\s+)?"
    r"(?:на\s+)?"
    r"(?:два(?:\s+(?:блок\w*|модул\w*|раздел\w*))?\s+)?"
    r"(.+?)\s+и\s+(.+?)(?:\.|$)",
    re.IGNORECASE,
)
_SPLIT_HINT_PATTERN = re.compile(
    r"(?:раздел\w*|раздели\w*|разбить|разбей|два\s+блок|два\s+модул|отдельн\w+\s+блок)",
    re.IGNORECASE,
)


def course_brief_interview_json_schema() -> Dict[str, Any]:
    """Возвращает schema для OpenRouter/OpenAI structured outputs."""
    return {
        "name": "course_brief_interview_result",
        "strict": True,
        "schema": CourseBriefInterviewResult.model_json_schema(),
    }


def model_dump(model: BaseModel) -> Dict[str, Any]:
    """Поддерживает Pydantic v2 и лёгкие совместимые тестовые объекты."""
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    return model.dict()


def validate_interview_result(
    raw_result: Any,
    answer: CourseBriefAnswerRequest,
    history: Iterable[Dict[str, Any]],
) -> CourseBriefInterviewResult:
    """Проверяет JSON модели, включая доказательства из реальных слов пользователя.

    Валидация специально консервативна: неизвестный формат, лишние поля,
    выдуманная цитата или неподходящее значение приводят к fallback, а не к
    сохранению неподтверждённого решения.
    """
    result = CourseBriefInterviewResult.model_validate(raw_result)
    _validate_signal_shape(result.signals)
    _validate_signal_relationships(result.signals)
    _validate_evidence(result.signals, answer, history)
    _validate_structure_request(result.structure_request, answer, history)
    _validate_model_question(result)
    return result


def _validate_signal_shape(signals: CourseBriefInterviewSignals) -> None:
    for name, allowed_values in SIGNAL_VALUES.items():
        signal = getattr(signals, name)
        if signal.status == CourseBriefSignalStatus.CONFIRMED:
            if signal.value not in allowed_values:
                raise ValueError(f"Неверное подтверждённое значение {name}")
        elif signal.value is not None:
            raise ValueError(f"У сигнала {name} без подтверждения не должно быть value")

        if signal.status == CourseBriefSignalStatus.NOT_APPLICABLE and signal.evidence:
            raise ValueError(f"У not_applicable сигнала {name} не должно быть evidence")


def _validate_signal_relationships(signals: CourseBriefInterviewSignals) -> None:
    necessity = signals.necessity
    others = (signals.depth, signals.knowledge, signals.application, signals.scope)
    if necessity.status == CourseBriefSignalStatus.NOT_APPLICABLE:
        raise ValueError("necessity не может быть not_applicable")

    if (
        necessity.status == CourseBriefSignalStatus.CONFIRMED
        and necessity.value == "exclude"
    ):
        if any(signal.status != CourseBriefSignalStatus.NOT_APPLICABLE for signal in others):
            raise ValueError("При исключении модуля остальные признаки not_applicable")
    elif any(signal.status == CourseBriefSignalStatus.NOT_APPLICABLE for signal in others):
        raise ValueError("not_applicable допустим только для исключённого модуля")


def _validate_evidence(
    signals: CourseBriefInterviewSignals,
    answer: CourseBriefAnswerRequest,
    history: Iterable[Dict[str, Any]],
) -> None:
    sources = _user_sources(answer, history)
    for name in SIGNAL_VALUES:
        signal = getattr(signals, name)
        for quote in signal.evidence:
            if not isinstance(quote, str) or not quote.strip() or not any(quote in source for source in sources):
                raise ValueError(f"Недопустимая цитата в evidence для {name}")

        if signal.status == CourseBriefSignalStatus.CONFIRMED:
            if signal.evidence:
                continue
            if not _is_directly_selected(name, signal.value, answer):
                raise ValueError(f"Для {name} не хватает подтверждения пользователя")
        elif signal.status == CourseBriefSignalStatus.CONFLICT and not signal.evidence:
            raise ValueError(f"Для conflict {name} требуется цитата")


def _validate_model_question(result: CourseBriefInterviewResult) -> None:
    question = result.follow_up_question
    if question is not None:
        question = question.strip()
    if result.action in {CourseBriefInterviewAction.ASK, CourseBriefInterviewAction.REVISE_GOAL}:
        if not question or len(question) > 300 or question.count("?") != 1:
            raise ValueError("Уточняющий вопрос должен содержать один вопросительный знак")
    elif question is not None:
        raise ValueError("Для перехода между модулями follow_up_question должен быть null")


def _validate_structure_request(
    request: CourseBriefStructureRequest,
    answer: CourseBriefAnswerRequest,
    history: Iterable[Dict[str, Any]],
) -> None:
    if request.kind == CourseBriefStructureChangeKind.NONE:
        if (
            request.ready
            or request.title
            or request.purpose
            or request.second_title
            or request.evidence
        ):
            raise ValueError("Пустой structure_request не должен содержать данные")
        return

    sources = _user_sources(answer, history)
    for quote in request.evidence:
        if not isinstance(quote, str) or not quote.strip() or not any(quote in source for source in sources):
            raise ValueError("Недопустимая цитата в evidence для structure_request")
    if request.kind == CourseBriefStructureChangeKind.ADD_MODULE:
        if request.ready and not (request.title or "").strip():
            raise ValueError("Готовый запрос нового раздела должен содержать title")
        return
    if request.kind == CourseBriefStructureChangeKind.SPLIT_MODULE:
        if request.ready and (
            not (request.title or "").strip() or not (request.second_title or "").strip()
        ):
            raise ValueError("Готовый split_module должен содержать title и second_title")
        return
    raise ValueError(f"Неизвестный kind structure_request: {request.kind}")


def _user_sources(
    answer: CourseBriefAnswerRequest,
    history: Iterable[Dict[str, Any]],
) -> List[str]:
    sources: List[str] = []
    if (answer.comment or "").strip():
        sources.append(answer.comment.strip())
    for item in history:
        if item.get("role") == "user" and isinstance(item.get("content"), str):
            sources.append(item["content"])
    return sources


def _is_directly_selected(
    name: str,
    value: Optional[str],
    answer: CourseBriefAnswerRequest,
) -> bool:
    if name == "necessity" and answer.depth is not None:
        expected = "exclude" if answer.depth == CourseBriefDepth.SKIP else "include"
        return value == expected
    if name == "depth" and answer.depth is not None and answer.depth != CourseBriefDepth.SKIP:
        return value == answer.depth.value
    if name == "knowledge" and answer.knowledge_level is not None:
        return value == answer.knowledge_level.value
    return False


def make_fallback_result(answer: CourseBriefAnswerRequest) -> CourseBriefInterviewResult:
    """Извлекает только явные варианты UI без сети и догадок.

    Этот путь нужен local demo и является безопасным fallback при недоступной
    модели. Текст не преобразуется в глубину или уровень эвристически: так
    демо не выдаёт предположение за решение пользователя.
    """
    missing = CourseBriefInterviewSignal(status=CourseBriefSignalStatus.MISSING)
    signals = CourseBriefInterviewSignals(
        necessity=missing.model_copy(deep=True),
        depth=missing.model_copy(deep=True),
        knowledge=missing.model_copy(deep=True),
        application=missing.model_copy(deep=True),
        scope=missing.model_copy(deep=True),
    )
    if answer.depth == CourseBriefDepth.SKIP:
        signals.necessity = CourseBriefInterviewSignal(
            status=CourseBriefSignalStatus.CONFIRMED,
            value="exclude",
        )
        for name in ("depth", "knowledge", "application", "scope"):
            setattr(
                signals,
                name,
                CourseBriefInterviewSignal(status=CourseBriefSignalStatus.NOT_APPLICABLE),
            )
    elif answer.depth is not None:
        signals.necessity = CourseBriefInterviewSignal(
            status=CourseBriefSignalStatus.CONFIRMED,
            value="include",
        )
        signals.depth = CourseBriefInterviewSignal(
            status=CourseBriefSignalStatus.CONFIRMED,
            value=answer.depth.value,
        )

    if answer.knowledge_level is not None and answer.depth != CourseBriefDepth.SKIP:
        signals.knowledge = CourseBriefInterviewSignal(
            status=CourseBriefSignalStatus.CONFIRMED,
            value=answer.knowledge_level.value,
        )
    return CourseBriefInterviewResult(
        signals=signals,
        action=CourseBriefInterviewAction.ASK,
        # Текст выбирает сервер после анализа всех gaps: так при полностью
        # неопределённом ответе первым будет вопрос о необходимости модуля.
        follow_up_question=None,
        structure_request=infer_structure_request_from_comment(answer.comment),
    )


def merge_signals(
    previous: Optional[Dict[str, Any]],
    current: CourseBriefInterviewSignals,
) -> CourseBriefInterviewSignals:
    """Сохраняет подтверждённые прежние ответы, пока новый ответ их не уточнил.

    Модель получает полную history и обычно сама вернёт итог. Слияние служит
    страховкой от её случайного пропуска ранее подтверждённого признака.
    """
    if not previous:
        return current
    try:
        old = CourseBriefInterviewSignals.model_validate(previous)
    except ValidationError:
        return current

    payload = model_dump(current)
    for name in SIGNAL_VALUES:
        old_signal = getattr(old, name)
        new_signal = getattr(current, name)
        if (
            new_signal.status == CourseBriefSignalStatus.MISSING
            and old_signal.status == CourseBriefSignalStatus.CONFIRMED
        ):
            payload[name] = model_dump(old_signal)
    return CourseBriefInterviewSignals.model_validate(payload)


def choose_server_action(
    signals: CourseBriefInterviewSignals,
    followup_count: int,
    max_followups: int,
    is_last_module: bool,
    included_modules_before_current: int,
    *,
    critical_signals: Optional[Tuple[str, ...]] = None,
) -> CourseBriefInterviewAction:
    """Детерминированно выбирает переход и не доверяет действию модели."""
    necessity = signals.necessity
    current_is_excluded = (
        necessity.status == CourseBriefSignalStatus.CONFIRMED
        and necessity.value == "exclude"
    )
    checked = critical_signals or MODULE_GATE_SIGNALS
    has_critical_gap = any(
        getattr(signals, name).status
        in {CourseBriefSignalStatus.MISSING, CourseBriefSignalStatus.CONFLICT}
        for name in checked
    )
    allowed_followups = min(max(max_followups, 0), MAX_MODULE_FOLLOWUPS)
    if has_critical_gap and not current_is_excluded and followup_count < allowed_followups:
        return CourseBriefInterviewAction.ASK

    current_is_included = (
        necessity.status == CourseBriefSignalStatus.CONFIRMED
        and necessity.value == "include"
    )
    if not is_last_module:
        return CourseBriefInterviewAction.NEXT_MODULE
    if current_is_included or included_modules_before_current > 0:
        return CourseBriefInterviewAction.FINISH
    return CourseBriefInterviewAction.REVISE_GOAL


def module_gate_complete(signals: CourseBriefInterviewSignals) -> bool:
    """Модуль можно детализировать по урокам: включён и gate-сигналы собраны."""
    if (
        signals.necessity.status == CourseBriefSignalStatus.CONFIRMED
        and signals.necessity.value == "exclude"
    ):
        return True
    return all(
        getattr(signals, name).status == CourseBriefSignalStatus.CONFIRMED
        for name in MODULE_GATE_SIGNALS
    )


def module_is_included(signals: CourseBriefInterviewSignals) -> bool:
    return (
        signals.necessity.status == CourseBriefSignalStatus.CONFIRMED
        and signals.necessity.value == "include"
    )


def lesson_scope_question(
    module_title: str,
    lesson_titles: Optional[List[str]] = None,
    knowledge_level: Optional[str] = None,
) -> str:
    """Первый вопрос фазы уроков: состав черновика уроков модуля."""
    titles = [
        title.strip()
        for title in (lesson_titles or [])
        if isinstance(title, str) and title.strip()
    ]
    level_hint = ""
    if knowledge_level:
        level_hint = f" Учтите заявленный уровень «{knowledge_level}»."
    if titles:
        listed = ", ".join(f"«{title}»" for title in titles)
        count_hint = f" Всего в черновике: {len(titles)}."
        return (
            f"Для блока «{module_title}» подготовлен черновик уроков: {listed}."
            f"{level_hint}{count_hint} "
            "Оставить все эти уроки или какие-то убрать либо заменить?"
        )
    return (
        f"В блоке «{module_title}» пока нет уроков.{level_hint} "
        "Какие уроки должны войти в этот блок?"
    )


def lesson_extras_question(
    module_title: str,
    other_topics: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Вопрос про дополнительную потребность в текущем блоке."""
    hint = ""
    if other_topics:
        samples = []
        for item in other_topics[:6]:
            title = (item.get("title") or "").strip()
            module_name = (item.get("module_title") or "").strip()
            if title and module_name:
                samples.append(f"«{title}» (уже в «{module_name}»)")
            elif title:
                samples.append(f"«{title}»")
        if samples:
            hint = (
                " Темы из других блоков не дублируйте без необходимости: "
                + ", ".join(samples)
                + "."
            )
    return (
        f"Чего ещё не хватает в блоке «{module_title}»: какие темы, практику или разбор "
        f"добавить именно сюда?{hint} Если ничего — напишите «ничего»."
    )


def comment_declines_extras(comment: Optional[str]) -> bool:
    """Ответ уже говорит, что дополнять блок не нужно.

    Сюда же относится явное принятие черновика уроков («все оставить»):
    состав подтверждён, отдельный вопрос про добавки не нужен.
    """
    text = (comment or "").strip().lower()
    if not text:
        return False

    # Короткие ответы — только точное совпадение всей фразы.
    # Нельзя искать «ок» подстрокой: оно входит в «урок».
    if text in {
        "ок",
        "окей",
        "ok",
        "okay",
        "хорошо",
        "подходит",
        "да",
        "норм",
        "нормально",
        "согласен",
        "согласна",
    }:
        return True

    decline_phrases = (
        "ничего не добав",
        "не добавляем",
        "не добавлять",
        "добавлять не",
        "ничего лишнего",
        "больше ничего",
        "больше не нужно",
        "достаточно",
        "хватает",
        "без дополн",
        "не нужно дополн",
        "все оставить",
        "всё оставить",
        "оставить все",
        "оставить всё",
        "все уроки",
        "все темы",
        "оставить как есть",
    )
    if any(phrase in text for phrase in decline_phrases):
        # «оставить все и добавить X» — extras всё же нужны,
        # кроме случая «добавь модуль/раздел»: это структурный запрос, не урок.
        structure = infer_structure_request_from_comment(comment)
        if structure.kind in {
            CourseBriefStructureChangeKind.ADD_MODULE,
            CourseBriefStructureChangeKind.SPLIT_MODULE,
        }:
            return True
        if any(
            token in text
            for token in ("добав", "ещё ", "еще ", "не хвата", "плюс ", "также ")
        ) and not any(
            token in text
            for token in ("не добавля", "ничего не добав", "без дополн")
        ):
            return False
        return True
    return False


def significant_topic_tokens(title: Optional[str]) -> set:
    """Значимые токены названия для мягкого сравнения тем."""
    stop = {
        "и",
        "или",
        "для",
        "про",
        "по",
        "с",
        "на",
        "в",
        "о",
        "об",
        "урок",
        "уроки",
        "тема",
        "темы",
        "модуль",
        "раздел",
        "блок",
        "основы",
        "практика",
        "данные",
        "данных",
        "работы",
        "работа",
    }
    tokens = set(re.findall(r"[a-zа-яё0-9]+", (title or "").lower()))
    return {token for token in tokens if len(token) > 3 and token not in stop}


def titles_are_similar(left: Optional[str], right: Optional[str]) -> bool:
    """Exact/substring или достаточное пересечение значимых токенов."""
    a = (left or "").strip().lower()
    b = (right or "").strip().lower()
    if not a or not b:
        return False
    if a == b or a in b or b in a:
        return True
    tokens_a = significant_topic_tokens(a)
    tokens_b = significant_topic_tokens(b)
    if not tokens_a or not tokens_b:
        return False
    overlap = len(tokens_a & tokens_b)
    return overlap >= 1 and overlap / min(len(tokens_a), len(tokens_b)) >= 0.5


def merge_session_structure_request(
    previous: Optional[Dict[str, Any]],
    current: CourseBriefStructureRequest,
    *,
    anchor_module_number: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """Объединяет сессионную очередь add/split с новым запросом из комментария."""
    if current.kind not in {
        CourseBriefStructureChangeKind.ADD_MODULE,
        CourseBriefStructureChangeKind.SPLIT_MODULE,
    }:
        return previous if isinstance(previous, dict) else None
    base = previous if isinstance(previous, dict) else {}
    previous_model = _parse_stored_structure_request(base)
    merged = merge_structure_request(previous_model, current)
    payload = model_dump(merged)
    payload["followup_count"] = int(base.get("followup_count") or 0)
    payload["awaiting_answer"] = False
    if anchor_module_number is not None:
        payload["anchor_module_number"] = anchor_module_number
    elif base.get("anchor_module_number") is not None:
        payload["anchor_module_number"] = base.get("anchor_module_number")
    return payload


def structure_request_ready_for_insert(
    pending: Optional[Dict[str, Any]],
    existing_titles: Iterable[str],
) -> Optional[str]:
    """Возвращает ask/insert/split или None для сессионной очереди структуры."""
    request = _parse_stored_structure_request(pending)
    if request is None:
        return None
    followup = 0
    if isinstance(pending, dict):
        try:
            followup = max(0, int(pending.get("followup_count") or 0))
        except (TypeError, ValueError):
            followup = 0
    split_action = choose_split_module_action(request, followup)
    if split_action:
        return split_action
    return choose_add_module_action(request, followup, existing_titles)


def is_clarifying_question(comment: Optional[str]) -> bool:
    """Пользователь спрашивает уточнение, а не отвечает по составу уроков."""
    text = (comment or "").strip()
    if not text:
        return False
    lowered = text.lower()
    # Явное решение по составу — не clarification.
    if any(
        token in lowered
        for token in (
            "оставить все",
            "оставить всё",
            "убр",
            "исключ",
            "замен",
            "ничего не добав",
            "не добавляем",
        )
    ):
        return False
    question_marks = "?" in text or "？" in text
    ask_tokens = (
        "что будет",
        "что входит",
        "что включает",
        "что в уроке",
        "какие темы",
        "расскажи",
        "поясни",
        "объясни",
        "что значит",
        "зачем ",
        "почему ",
        "как устроен",
        "подробнее",
        "что такое",
    )
    if any(token in lowered for token in ask_tokens):
        return True
    # Короткий вопрос без явного решения по составу.
    return question_marks and len(text) <= 180


def match_lesson_by_comment(
    comment: Optional[str],
    lessons: Iterable[Any],
) -> Optional[Any]:
    """Ищет урок, о котором спрашивает пользователь."""
    text = (comment or "").strip().lower()
    if not text:
        return None
    best = None
    best_len = 0
    for lesson in lessons:
        title = getattr(lesson, "lesson_title", None) or (
            lesson.get("lesson_title") if isinstance(lesson, dict) else None
        )
        if not title:
            continue
        key = str(title).strip().lower()
        if key and key in text and len(key) > best_len:
            best = lesson
            best_len = len(key)
    return best


def describe_lesson_brief(lesson: Any) -> str:
    """Кратко описывает черновик урока для ответа на уточнение."""
    title = getattr(lesson, "lesson_title", None) or (
        lesson.get("lesson_title") if isinstance(lesson, dict) else "урок"
    )
    goal = getattr(lesson, "lesson_goal", None) or (
        lesson.get("lesson_goal") if isinstance(lesson, dict) else None
    )
    outline = getattr(lesson, "content_outline", None) or (
        lesson.get("content_outline") if isinstance(lesson, dict) else None
    )
    parts = [f"В уроке «{title}»"]
    if goal:
        parts.append(f"цель: {str(goal).rstrip('.')}.")
    else:
        parts.append("пока зафиксирована только тема.")
    if isinstance(outline, list) and outline:
        bullets = "; ".join(str(item).strip() for item in outline[:5] if str(item).strip())
        if bullets:
            parts.append(f"В плане: {bullets}.")
    parts.append("Это черновик: детали появятся при генерации контента.")
    return " ".join(parts)


def clarifying_reply_for_lessons(
    comment: Optional[str],
    lessons: Iterable[Any],
    *,
    follow_up_question: str,
) -> str:
    """Отвечает на уточнение и снова задаёт рабочий вопрос фазы."""
    lesson_list = list(lessons)
    matched = match_lesson_by_comment(comment, lesson_list)
    if matched is not None:
        explanation = describe_lesson_brief(matched)
    elif lesson_list:
        snippets = []
        for lesson in lesson_list[:4]:
            title = getattr(lesson, "lesson_title", None) or (
                lesson.get("lesson_title") if isinstance(lesson, dict) else None
            )
            goal = getattr(lesson, "lesson_goal", None) or (
                lesson.get("lesson_goal") if isinstance(lesson, dict) else None
            )
            if title and goal:
                snippets.append(f"«{title}» — {goal}")
            elif title:
                snippets.append(f"«{title}»")
        explanation = (
            "Кратко по черновику блока: " + "; ".join(snippets) + "."
            if snippets
            else "В черновике пока мало деталей по урокам."
        )
    else:
        explanation = "В этом блоке пока нет черновика уроков."
    return f"{explanation} {follow_up_question}"


def snapshot_lesson_promise(lesson: Any, *, source: str = "clarification") -> Dict[str, Any]:
    """Фиксирует обещанные детали урока, показанные пользователю."""
    title = getattr(lesson, "lesson_title", None) or (
        lesson.get("lesson_title") if isinstance(lesson, dict) else None
    )
    goal = getattr(lesson, "lesson_goal", None) or (
        lesson.get("lesson_goal") if isinstance(lesson, dict) else None
    )
    outline = getattr(lesson, "content_outline", None) or (
        lesson.get("content_outline") if isinstance(lesson, dict) else None
    )
    cleaned_outline: List[str] = []
    if isinstance(outline, list):
        cleaned_outline = [str(item).strip() for item in outline if str(item).strip()]
    return {
        "title": str(title or "").strip(),
        "promised_goal": str(goal).strip() if goal else None,
        "promised_outline": cleaned_outline,
        "source": source,
    }


def merge_lesson_promises(
    existing: Optional[Iterable[Dict[str, Any]]],
    new_items: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Объединяет обещания по названию урока (новые перекрывают старые)."""
    merged: Dict[str, Dict[str, Any]] = {}
    for item in list(existing or []) + list(new_items):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        merged[title.lower()] = {
            "title": title,
            "promised_goal": item.get("promised_goal"),
            "promised_outline": list(item.get("promised_outline") or [])
            if isinstance(item.get("promised_outline"), list)
            else [],
            "source": item.get("source") or "clarification",
        }
    return list(merged.values())


def collect_other_module_topics(
    draft_modules: Iterable[Any],
    current_module_number: int,
) -> List[Dict[str, Any]]:
    """Каталог уроков других модулей для антидублей."""
    topics: List[Dict[str, Any]] = []
    for module in draft_modules:
        number = getattr(module, "module_number", None)
        if number == current_module_number:
            continue
        module_title = getattr(module, "module_title", "") or ""
        lessons = getattr(module, "lessons", None) or []
        for lesson in lessons:
            title = getattr(lesson, "lesson_title", None) or (
                lesson.get("lesson_title") if isinstance(lesson, dict) else None
            )
            if not title:
                continue
            topics.append(
                {
                    "title": str(title).strip(),
                    "module_number": number,
                    "module_title": module_title,
                }
            )
    return topics


def find_duplicate_topics(
    requested_titles: Iterable[str],
    other_topics: Iterable[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Находит запрошенные темы, которые уже есть в других модулях."""
    catalog = [
        item
        for item in other_topics
        if (item.get("title") or "").strip()
    ]
    duplicates: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for title in requested_titles:
        key = (title or "").strip().lower()
        if not key or key in seen:
            continue
        match = None
        for item in catalog:
            if titles_are_similar(title, item.get("title")):
                match = item
                break
        if match is not None:
            seen.add(key)
            duplicates.append(
                {
                    "requested": title.strip(),
                    "existing_title": match.get("title"),
                    "module_number": match.get("module_number"),
                    "module_title": match.get("module_title"),
                }
            )
    return duplicates


def count_similar_topic_modules(
    title: str,
    draft_modules: Iterable[Any],
    *,
    exclude_module_number: Optional[int] = None,
) -> int:
    """Сколько других модулей уже содержат похожую тему-урок."""
    count = 0
    for module in draft_modules:
        number = getattr(module, "module_number", None)
        if exclude_module_number is not None and number == exclude_module_number:
            continue
        lessons = getattr(module, "lessons", None) or []
        for lesson in lessons:
            lesson_title = getattr(lesson, "lesson_title", None) or (
                lesson.get("lesson_title") if isinstance(lesson, dict) else None
            )
            if titles_are_similar(title, lesson_title):
                count += 1
                break
    return count


def should_promote_topic_to_module(
    title: str,
    draft_modules: Iterable[Any],
    *,
    current_module_number: int,
    theme_mentions: Optional[Iterable[Dict[str, Any]]] = None,
) -> bool:
    """Тема уже всплывала в другом блоке — лучше отдельный модуль, чем ещё один урок."""
    if count_similar_topic_modules(
        title,
        draft_modules,
        exclude_module_number=current_module_number,
    ) >= 1:
        return True
    mentions = 0
    for item in theme_mentions or []:
        if not isinstance(item, dict):
            continue
        if item.get("module_number") == current_module_number:
            continue
        if titles_are_similar(title, item.get("title")):
            mentions += 1
    return mentions >= 1


def parse_excluded_lessons_from_comment(
    comment: Optional[str],
    lesson_titles: Iterable[str],
) -> List[str]:
    """Грубо определяет, какие уроки пользователь просит убрать."""
    text = (comment or "").strip().lower()
    if not text:
        return []
    if any(token in text for token in ("все оставить", "оставить все", "все уроки", "целиком")):
        return []
    excluded: List[str] = []
    for title in lesson_titles:
        normalized = (title or "").strip()
        if not normalized:
            continue
        if normalized.lower() in text and any(
            token in text for token in ("убр", "исключ", "не нуж", "без ", "убери")
        ):
            excluded.append(normalized)
    return excluded


def parse_extra_topics_from_comment(comment: Optional[str]) -> List[str]:
    """Достаёт кандидатов на дополнительные темы из свободного ответа."""
    text = (comment or "").strip()
    if not text:
        return []
    lowered = text.lower()
    if lowered in {"нет", "ничего", "не нужно", "достаточно", "-"}:
        return []
    parts = re.split(r"[,;/\n]| и | а также ", text)
    topics: List[str] = []
    for part in parts:
        cleaned = part.strip(" .,:;—-")
        if len(cleaned) < 2 or len(cleaned) > 80:
            continue
        if cleaned.lower() in {"нет", "ничего", "добавить", "хочу"}:
            continue
        topics.append(cleaned)
    return topics[:6]


def build_lesson_decisions(
    lesson_titles: Iterable[str],
    *,
    excluded: Optional[Iterable[str]] = None,
    knowledge_level: Optional[str] = None,
    comment: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Фиксирует решение по каждому уроку черновика модуля."""
    excluded_set = {(item or "").strip().lower() for item in (excluded or [])}
    decisions: List[Dict[str, Any]] = []
    for title in lesson_titles:
        normalized = (title or "").strip()
        if not normalized:
            continue
        include = normalized.lower() not in excluded_set
        decisions.append(
            {
                "title": normalized,
                "include": include,
                "knowledge_level": knowledge_level if include else None,
                "note": comment if include and comment else None,
            }
        )
    return decisions


def default_question_for_missing(
    signals: CourseBriefInterviewSignals,
    lesson_titles: Optional[List[str]] = None,
) -> str:
    """Возвращает один безопасный вопрос для local fallback."""
    for name, question in (
        ("necessity", "Нужен ли этот раздел для вашей цели: включить его или исключить?"),
        ("depth", "Какую глубину разбора этого раздела вы хотите: кратко, стандартно или глубоко?"),
        ("knowledge", "Как вы оцениваете свой текущий уровень в теме этого раздела?"),
    ):
        signal = getattr(signals, name)
        if signal.status in {CourseBriefSignalStatus.MISSING, CourseBriefSignalStatus.CONFLICT}:
            return question
    if signals.scope.status in {CourseBriefSignalStatus.MISSING, CourseBriefSignalStatus.CONFLICT}:
        return scope_question_for_lessons(lesson_titles)
    return "Какую цель курса вы хотите уточнить?"


def primary_missing_signal(
    signals: CourseBriefInterviewSignals,
    critical_signals: Optional[Tuple[str, ...]] = None,
) -> Optional[str]:
    """Возвращает первый критичный пробел для follow-up вопроса."""
    for name in critical_signals or MODULE_GATE_SIGNALS:
        signal = getattr(signals, name)
        if signal.status in {CourseBriefSignalStatus.MISSING, CourseBriefSignalStatus.CONFLICT}:
            return name
    return None


def scope_question_for_lessons(
    lesson_titles: Optional[List[str]] = None,
    requested_topics: Optional[List[str]] = None,
) -> str:
    """Спрашивает про состав раздела и всегда перечисляет известные уроки."""
    titles = [
        title.strip()
        for title in (lesson_titles or [])
        if isinstance(title, str) and title.strip()
    ]
    extras = [
        topic.strip()
        for topic in (requested_topics or [])
        if isinstance(topic, str) and topic.strip()
    ]
    if titles:
        listed = ", ".join(f"«{title}»" for title in titles)
        count_hint = f" Всего: {len(titles)}."
        if extras:
            wanted = ", ".join(f"«{topic}»" for topic in extras[:4])
            return (
                f"Сейчас в разделе заложены темы: {listed}.{count_hint} "
                f"Вы также назвали {wanted}. "
                "Оставить текущий список, добавить названное к нему "
                "или заменить часть тем?"
            )
        return (
            f"Сейчас в разделе заложены темы: {listed}.{count_hint} "
            "Оставить все или какие-то убрать либо заменить?"
        )
    if extras:
        wanted = ", ".join(f"«{topic}»" for topic in extras[:4])
        return (
            f"Вы назвали {wanted}. Какие ещё темы должны войти в этот раздел, "
            "а какие не нужны?"
        )
    return (
        "Этот раздел нужен целиком или только отдельные темы? "
        "Если не целиком — какие именно?"
    )


def apply_answer_buttons_to_signals(
    signals: CourseBriefInterviewSignals,
    answer: CourseBriefAnswerRequest,
) -> CourseBriefInterviewSignals:
    """Подтверждает признаки из кнопок UI, даже если модель их пропустила."""
    payload = model_dump(signals)
    if answer.depth == CourseBriefDepth.SKIP:
        payload["necessity"] = {
            "status": CourseBriefSignalStatus.CONFIRMED.value,
            "value": "exclude",
            "evidence": [],
        }
        for name in ("depth", "knowledge", "application", "scope"):
            payload[name] = {
                "status": CourseBriefSignalStatus.NOT_APPLICABLE.value,
                "value": None,
                "evidence": [],
            }
    elif answer.depth is not None:
        payload["necessity"] = {
            "status": CourseBriefSignalStatus.CONFIRMED.value,
            "value": "include",
            "evidence": [],
        }
        payload["depth"] = {
            "status": CourseBriefSignalStatus.CONFIRMED.value,
            "value": answer.depth.value,
            "evidence": [],
        }
    if answer.knowledge_level is not None and answer.depth != CourseBriefDepth.SKIP:
        payload["knowledge"] = {
            "status": CourseBriefSignalStatus.CONFIRMED.value,
            "value": answer.knowledge_level.value,
            "evidence": [],
        }
        if payload.get("scope", {}).get("status") == CourseBriefSignalStatus.NOT_APPLICABLE.value:
            payload["scope"] = {
                "status": CourseBriefSignalStatus.MISSING.value,
                "value": None,
                "evidence": [],
            }
    return CourseBriefInterviewSignals.model_validate(payload)


def apply_comment_hints_to_signals(
    signals: CourseBriefInterviewSignals,
    comment: Optional[str],
) -> CourseBriefInterviewSignals:
    """Добирает depth/knowledge из короткого текстового ответа на follow-up.

    Нужно, когда UI спросил уровень текстом, а пользователь ответил
    «начальный» / «средний» без нажатия кнопки.
    """
    text = (comment or "").strip().lower()
    if not text:
        return signals
    payload = model_dump(signals)

    if payload.get("knowledge", {}).get("status") in {
        CourseBriefSignalStatus.MISSING.value,
        CourseBriefSignalStatus.CONFLICT.value,
    }:
        knowledge_value = None
        if any(token in text for token in ("начальн", "начинающ", "новичок", "junior", "с нуля")):
            knowledge_value = "junior"
        elif any(token in text for token in ("продвинут", "senior", "эксперт", "опытн")):
            knowledge_value = "senior"
        elif any(token in text for token in ("средн", "middle", "есть практик", "есть опыт")):
            knowledge_value = "middle"
        if knowledge_value:
            payload["knowledge"] = {
                "status": CourseBriefSignalStatus.CONFIRMED.value,
                "value": knowledge_value,
                "evidence": [comment.strip()] if (comment or "").strip() else [],
            }

    if payload.get("depth", {}).get("status") in {
        CourseBriefSignalStatus.MISSING.value,
        CourseBriefSignalStatus.CONFLICT.value,
    }:
        depth_value = None
        if any(token in text for token in ("пропуст", "не нуж", "исключ", "skip")):
            depth_value = "skip"
        elif any(token in text for token in ("глубок", "подробн", "с кейс", "deep")):
            depth_value = "deep"
        elif any(token in text for token in ("кратк", "обзор", "brief")):
            depth_value = "brief"
        elif any(token in text for token in ("стандарт", "рабоч", "обычн")):
            depth_value = "standard"
        if depth_value == "skip":
            payload["necessity"] = {
                "status": CourseBriefSignalStatus.CONFIRMED.value,
                "value": "exclude",
                "evidence": [comment.strip()] if (comment or "").strip() else [],
            }
            for name in ("depth", "knowledge", "application", "scope"):
                payload[name] = {
                    "status": CourseBriefSignalStatus.NOT_APPLICABLE.value,
                    "value": None,
                    "evidence": [],
                }
        elif depth_value:
            payload["necessity"] = {
                "status": CourseBriefSignalStatus.CONFIRMED.value,
                "value": "include",
                "evidence": [],
            }
            payload["depth"] = {
                "status": CourseBriefSignalStatus.CONFIRMED.value,
                "value": depth_value,
                "evidence": [comment.strip()] if (comment or "").strip() else [],
            }

    return CourseBriefInterviewSignals.model_validate(payload)


def is_vague_topic_question(
    question: Optional[str],
    lesson_titles: Optional[List[str]] = None,
) -> bool:
    """Определяет вопрос про состав раздела без перечисления уроков."""
    text = (question or "").strip()
    if not text:
        return False
    lowered = text.lower()
    mentions_topics = any(
        token in lowered
        for token in (
            "все темы",
            "все уроки",
            "некоторые",
            "какие темы",
            "какие уроки",
            "темы раздела",
            "темы модуля",
            "уроки раздела",
            "уроки модуля",
            "состав раздела",
            "оставить все",
            "изучить все",
        )
    )
    if not mentions_topics:
        return False
    return not question_lists_lessons(text, lesson_titles)


def question_lists_lessons(question: str, lesson_titles: Optional[List[str]] = None) -> bool:
    """Проверяет, что вопрос реально называет уроки текущего раздела."""
    text = (question or "").lower()
    titles = [
        title.strip().lower()
        for title in (lesson_titles or [])
        if isinstance(title, str) and title.strip()
    ]
    if not titles:
        return True
    return any(title in text for title in titles)


def extract_requested_topics(
    comment: Optional[str],
    lesson_titles: Optional[List[str]] = None,
) -> List[str]:
    """Выделяет из комментария темы, которых ещё нет в уроках раздела."""
    text = (comment or "").strip()
    if not text:
        return []
    known = {
        title.strip().lower()
        for title in (lesson_titles or [])
        if isinstance(title, str) and title.strip()
    }
    candidates: List[str] = []
    # Короткие технические термины и фразы после «с/про/добавить».
    for match in re.finditer(
        r"(?:добав\w*|нужен|нужно|ещё|еще|про|с(?:\s+использованием)?)\s+([A-Za-zА-Яа-я0-9_+\- ]{2,40})",
        text,
        flags=re.IGNORECASE,
    ):
        topic = match.group(1).strip(" .,:;—-")
        if topic and topic.lower() not in known and topic.lower() not in {
            item.lower() for item in candidates
        }:
            candidates.append(topic)
    if not candidates:
        # Если весь комментарий короткий и не совпадает с уроком — это и есть тема.
        compact = text.strip(" .,:;—-")
        if (
            2 <= len(compact) <= 60
            and compact.lower() not in known
            and "модул" not in compact.lower()
            and "раздел" not in compact.lower()
        ):
            candidates.append(compact)
    return candidates[:4]


def infer_structure_request_from_comment(comment: Optional[str]) -> CourseBriefStructureRequest:
    """Достаёт запрос add/split из текста, если модель недоступна."""
    text = (comment or "").strip()
    if not text:
        return CourseBriefStructureRequest()

    split_match = _SPLIT_MODULE_PATTERN.search(text)
    if split_match is not None or _SPLIT_HINT_PATTERN.search(text):
        title = None
        second_title = None
        if split_match is not None:
            title = _clean_structure_title(split_match.group(1))
            second_title = _clean_structure_title(split_match.group(2))
            # Обрезаем хвост вроде «Это должны быть два блока».
            if second_title:
                second_title = re.split(
                    r"\bэто\b|\bдолжны\b|\bдолжн\w*\b",
                    second_title,
                    maxsplit=1,
                    flags=re.IGNORECASE,
                )[0].strip(" .,:;—-")
                second_title = _clean_structure_title(second_title)
        return CourseBriefStructureRequest(
            kind=CourseBriefStructureChangeKind.SPLIT_MODULE,
            title=title,
            second_title=second_title,
            purpose=None,
            ready=bool(title and second_title),
            evidence=[text],
        )

    match = _ADD_MODULE_PATTERN.search(text)
    lowered = text.lower()
    # Без явного «модуль/раздел» не считаем ADD_MODULE: иначе «добавь урок/тему»
    # ложно уходит в новый раздел курса.
    if match is None and not any(
        token in lowered
        for token in (
            "новый раздел",
            "новый модуль",
            "отдельный раздел",
            "отдельный модуль",
            "отдельным разделом",
            "отдельным модулем",
        )
    ):
        return CourseBriefStructureRequest()
    title = _clean_structure_title(match.group(1)) if match else None
    return CourseBriefStructureRequest(
        kind=CourseBriefStructureChangeKind.ADD_MODULE,
        title=title,
        purpose=None,
        ready=False,
        evidence=[text],
    )


def _clean_structure_title(value: Optional[str]) -> Optional[str]:
    title = (value or "").strip(" .,:;—-«»\"'")
    if not title:
        return None
    if len(title) > 120:
        title = title[:120].rstrip()
    return title


def parse_split_titles_from_comment(comment: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Достаёт два названия блоков из ответа на уточнение split."""
    text = (comment or "").strip()
    if not text:
        return None, None
    match = _SPLIT_MODULE_PATTERN.search(text)
    if match:
        return _clean_structure_title(match.group(1)), _clean_structure_title(match.group(2))
    # «A» и «B» / A / B / A и B
    quoted = re.findall(r"[«\"]([^»\"]+)[»\"]", text)
    if len(quoted) >= 2:
        return _clean_structure_title(quoted[0]), _clean_structure_title(quoted[1])
    parts = re.split(r"\s+и\s+|/", text, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) == 2:
        return _clean_structure_title(parts[0]), _clean_structure_title(parts[1])
    return None, None


def merge_structure_request(
    previous: Optional[Dict[str, Any]],
    current: CourseBriefStructureRequest,
) -> CourseBriefStructureRequest:
    """Сохраняет незавершённый запрос изменения структуры между шагами."""
    previous_request = _parse_stored_structure_request(previous)
    if current.kind == CourseBriefStructureChangeKind.ADD_MODULE:
        if previous_request is None or previous_request.kind != CourseBriefStructureChangeKind.ADD_MODULE:
            return current
        title = (current.title or previous_request.title or "").strip() or None
        purpose = (current.purpose or previous_request.purpose or "").strip() or None
        evidence = current.evidence or previous_request.evidence
        return CourseBriefStructureRequest(
            kind=CourseBriefStructureChangeKind.ADD_MODULE,
            title=title,
            purpose=purpose,
            second_title=None,
            ready=current.ready or bool(title and purpose),
            evidence=evidence,
        )
    if current.kind == CourseBriefStructureChangeKind.SPLIT_MODULE:
        if previous_request is None or previous_request.kind != CourseBriefStructureChangeKind.SPLIT_MODULE:
            return current
        title = (current.title or previous_request.title or "").strip() or None
        second_title = (
            current.second_title or previous_request.second_title or ""
        ).strip() or None
        evidence = current.evidence or previous_request.evidence
        return CourseBriefStructureRequest(
            kind=CourseBriefStructureChangeKind.SPLIT_MODULE,
            title=title,
            purpose=None,
            second_title=second_title,
            ready=current.ready or bool(title and second_title),
            evidence=evidence,
        )
    if previous_request is not None and previous_request.kind in {
        CourseBriefStructureChangeKind.ADD_MODULE,
        CourseBriefStructureChangeKind.SPLIT_MODULE,
    }:
        # Пользователь отвечает на уточнение текстом без kind от модели.
        if previous_request.kind == CourseBriefStructureChangeKind.SPLIT_MODULE:
            first, second = parse_split_titles_from_comment(
                " ".join(current.evidence) if current.evidence else None
            )
            # evidence может быть пустым — парсим не из current; вызывающий код
            # дополнительно мержит comment отдельно при необходимости.
            title = first or previous_request.title
            second_title = second or previous_request.second_title
            return CourseBriefStructureRequest(
                kind=CourseBriefStructureChangeKind.SPLIT_MODULE,
                title=title,
                second_title=second_title,
                purpose=None,
                ready=bool(title and second_title),
                evidence=previous_request.evidence,
            )
        return previous_request
    return current


def enrich_pending_structure_from_comment(
    pending: CourseBriefStructureRequest,
    comment: Optional[str],
) -> CourseBriefStructureRequest:
    """Добирает поля незавершённого structure_request из текста ответа."""
    text = (comment or "").strip()
    if not text:
        return pending
    if pending.kind == CourseBriefStructureChangeKind.SPLIT_MODULE:
        first, second = parse_split_titles_from_comment(text)
        title = first or pending.title
        second_title = second or pending.second_title
        if not first and not second and not pending.title:
            # Одно название в ответе — считаем первым блоком.
            title = _clean_structure_title(text)
        elif not second and pending.title and first and not second:
            second_title = first
            title = pending.title
        return CourseBriefStructureRequest(
            kind=CourseBriefStructureChangeKind.SPLIT_MODULE,
            title=title,
            second_title=second_title,
            purpose=None,
            ready=bool(title and second_title),
            evidence=list(pending.evidence or []) or [text],
        )
    if pending.kind == CourseBriefStructureChangeKind.ADD_MODULE:
        title = pending.title
        purpose = pending.purpose
        if not title:
            title = _clean_structure_title(text)
        elif not purpose:
            purpose = text[:300]
        return CourseBriefStructureRequest(
            kind=CourseBriefStructureChangeKind.ADD_MODULE,
            title=title,
            purpose=purpose,
            second_title=None,
            ready=bool(title and purpose),
            evidence=list(pending.evidence or []) or [text],
        )
    return pending


def _parse_stored_structure_request(
    payload: Optional[Dict[str, Any]],
) -> Optional[CourseBriefStructureRequest]:
    if not isinstance(payload, dict):
        return None
    data = {
        key: value
        for key, value in payload.items()
        if key
        not in {
            "followup_count",
            "awaiting_answer",
            "anchor_module_number",
        }
    }
    try:
        return CourseBriefStructureRequest.model_validate(data)
    except ValidationError:
        return None


def choose_add_module_action(
    request: CourseBriefStructureRequest,
    followup_count: int,
    existing_titles: Iterable[str],
) -> Optional[str]:
    """Возвращает ask, insert или None. Не доверяет флагу ready модели в одиночку."""
    if request.kind != CourseBriefStructureChangeKind.ADD_MODULE:
        return None
    title = (request.title or "").strip()
    purpose = (request.purpose or "").strip()
    normalized_existing = {item.strip().lower() for item in existing_titles if item and item.strip()}
    if title and title.lower() in normalized_existing:
        return None
    if followup_count >= MAX_ADD_MODULE_FOLLOWUPS:
        return "insert" if title else None
    if not title or not purpose:
        return "ask"
    return "insert"


def choose_split_module_action(
    request: CourseBriefStructureRequest,
    followup_count: int,
) -> Optional[str]:
    """Возвращает ask, split или None для разделения текущего блока."""
    if request.kind != CourseBriefStructureChangeKind.SPLIT_MODULE:
        return None
    title = (request.title or "").strip()
    second_title = (request.second_title or "").strip()
    if title and second_title and title.lower() != second_title.lower():
        return "split"
    if followup_count >= MAX_SPLIT_MODULE_FOLLOWUPS:
        return None
    return "ask"


def add_module_question(request: CourseBriefStructureRequest) -> str:
    """Вопрос для 1–2 уточнений перед вставкой нового раздела."""
    if not (request.title or "").strip():
        return "Как назвать новый раздел, который вы хотите добавить в курс?"
    return f"Что должно войти в раздел «{request.title.strip()}» и зачем он вам нужен?"


def split_module_question(
    request: CourseBriefStructureRequest,
    current_module_title: str,
) -> str:
    """Вопрос для уточнения названий после запроса разделить блок."""
    title = (request.title or "").strip()
    second = (request.second_title or "").strip()
    if not title and not second:
        return (
            f"Раздел «{current_module_title}» разобьём на два блока. "
            "Как назвать первый и второй? Например: «Основы BPMN» и «Введение в Camunda»."
        )
    if title and not second:
        return (
            f"Первый блок — «{title}». Как назвать второй блок после разделения?"
        )
    if second and not title:
        return (
            f"Второй блок — «{second}». Как назвать первый блок после разделения?"
        )
    return (
        f"Подтвердите названия после разделения: «{title}» и «{second}». "
        "Если верно — напишите «да», иначе пришлите оба названия заново."
    )


def confidence_from_signals(signals: Optional[Dict[str, Any]]) -> Tuple[int, int]:
    """Возвращает процент полноты и количество confirmed-сигналов.

    Явно исключённый модуль является полностью принятым решением (100%), хотя
    это не означает, что итоговый курс содержит такой модуль.
    """
    if not signals:
        return 0, 0
    try:
        parsed = CourseBriefInterviewSignals.model_validate(signals)
    except ValidationError:
        return 0, 0

    if (
        parsed.necessity.status == CourseBriefSignalStatus.CONFIRMED
        and parsed.necessity.value == "exclude"
    ):
        return 100, 1

    percentage = 0
    confirmed = 0
    for name, weight in SIGNAL_WEIGHTS.items():
        if getattr(parsed, name).status == CourseBriefSignalStatus.CONFIRMED:
            percentage += weight
            confirmed += 1
    return percentage, confirmed


def signals_to_dict(signals: CourseBriefInterviewSignals) -> Dict[str, Any]:
    """Сериализует сигналы для JSON-поля decisions."""
    return model_dump(signals)
