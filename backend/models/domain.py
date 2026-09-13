"""
Доменные модели данных (Pydantic)
Адаптировано из TGBotCreateCourse проекта
"""
from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Union
from enum import Enum
from datetime import datetime


class DifficultyLevel(str, Enum):
    """Уровень сложности курса"""
    JUNIOR = "junior"
    MIDDLE = "middle"
    SENIOR = "senior"


class CourseBriefDepth(str, Enum):
    """Желаемая глубина проработки раздела в интервью."""
    SKIP = "skip"
    BRIEF = "brief"
    STANDARD = "standard"
    DEEP = "deep"


class CourseBriefStatus(str, Enum):
    """Статус сессии уточнения структуры курса."""
    QUESTIONING = "questioning"
    COMPLETED = "completed"


class CourseBriefQuestionKind(str, Enum):
    """Тип вопроса, который сейчас ожидает интервью."""

    MODULE = "module"
    FOLLOW_UP = "follow_up"
    REVISE_GOAL = "revise_goal"
    ADD_MODULE = "add_module"
    SPLIT_MODULE = "split_module"
    LESSON_SCOPE = "lesson_scope"
    LESSON_EXTRAS = "lesson_extras"


class CourseBriefAnswerControls(str, Enum):
    """Какие элементы ответа показать в UI для текущего вопроса."""

    MODULE_GATE = "module_gate"
    KNOWLEDGE = "knowledge"
    DEPTH = "depth"
    TEXT = "text"


class CourseBriefModulePhase(str, Enum):
    """Фаза уточнения внутри одного модуля черновика."""

    MODULE_GATE = "module_gate"
    LESSON_SCOPE = "lesson_scope"
    LESSON_EXTRAS = "lesson_extras"
    DONE = "done"


class LessonFormat(str, Enum):
    """Формат урока"""
    THEORY = "theory"
    PRACTICE = "practice"
    LAB = "lab"
    QUIZ = "quiz"
    PROJECT = "project"


class SlideType(str, Enum):
    """Тип слайда в презентации"""
    TITLE = "title"
    CONTENT = "content"
    CODE = "code"
    DIAGRAM = "diagram"
    QUIZ = "quiz"
    SUMMARY = "summary"


# ============================================================================
# МОДЕЛИ ДЛЯ УЧЕБНЫХ МАТЕРИАЛОВ
# ============================================================================

class TopicMaterial(BaseModel):
    """Детальный учебный материал по отдельной теме из плана урока"""
    topic_title: str = Field(..., description="Название темы")
    topic_number: int = Field(..., ge=1, description="Порядковый номер темы")
    
    # Основной контент
    introduction: str = Field(..., description="Введение в тему (2-3 абзаца)")
    theory: str = Field(..., description="Теоретический материал")
    examples: List[str] = Field(default_factory=list, description="Практические примеры")
    code_snippets: Optional[List[str]] = Field(default=None, description="Примеры кода")
    
    # Дополнительные материалы
    key_points: List[str] = Field(default_factory=list, description="Ключевые моменты")
    common_mistakes: List[str] = Field(default_factory=list, description="Частые ошибки")
    best_practices: List[str] = Field(default_factory=list, description="Лучшие практики")
    
    # Задания и вопросы
    practice_exercises: List[str] = Field(default_factory=list, description="Упражнения")
    quiz_questions: List[str] = Field(default_factory=list, description="Вопросы для проверки")
    
    # Ссылки и ресурсы
    additional_resources: Optional[List[str]] = Field(default=None, description="Доп. ресурсы")
    estimated_reading_time_minutes: int = Field(default=25, description="Время изучения")


class LessonContent(BaseModel):
    """Полный контент урока с детализацией каждой темы"""
    lesson_title: str
    lesson_goal: str
    lesson_number: int
    module_number: int
    
    topics: List[TopicMaterial] = Field(default_factory=list)
    
    total_topics: int = Field(default=0)
    total_estimated_time_minutes: int = Field(default=0)


class QuestionOption(BaseModel):
    """Вариант ответа на вопрос теста"""
    option_text: str = Field(..., description="Текст варианта ответа")
    is_correct: bool = Field(default=False, description="Правильный ли это вариант")


class TestQuestion(BaseModel):
    """Вопрос теста"""
    question_text: str = Field(..., description="Текст вопроса")
    options: List[QuestionOption] = Field(..., description="Варианты ответов (минимум 2, максимум 6)")
    explanation: Optional[str] = Field(default=None, description="Объяснение правильного ответа")


class LessonTest(BaseModel):
    """Тест для урока"""
    lesson_title: str = Field(..., description="Название урока")
    lesson_goal: str = Field(..., description="Цель урока")
    questions: List[TestQuestion] = Field(..., description="Вопросы теста")
    total_questions: int = Field(default=0, description="Общее количество вопросов")
    passing_score_percent: int = Field(default=70, ge=0, le=100, description="Процент для прохождения теста")


class Lesson(BaseModel):
    """Урок в модуле курса"""
    lesson_title: str = Field(..., description="Название урока")
    lesson_goal: str = Field(..., description="Цель урока")
    content_outline: List[str] = Field(default_factory=list, description="План контента")
    assessment: str = Field(default="Тест", description="Метод оценки")
    format: Union[LessonFormat, str] = Field(default=LessonFormat.THEORY)
    estimated_time_minutes: int = Field(default=60, ge=15, le=480)
    
    # Опциональный детальный контент
    detailed_content: Optional[LessonContent] = None
    
    # Информация о видео
    video_id: Optional[str] = Field(default=None, description="ID видео в HeyGen")
    video_download_url: Optional[str] = Field(default=None, description="URL для скачивания видео")
    video_status: Optional[str] = Field(default=None, description="Статус видео (generating, completed, failed)")
    video_generated_at: Optional[datetime] = Field(default=None, description="Дата генерации видео")
    
    # Информация о тесте
    test: Optional[LessonTest] = Field(default=None, description="Тест для урока")


class Module(BaseModel):
    """Модуль курса"""
    module_number: int = Field(..., ge=1, description="Номер модуля")
    module_title: str = Field(..., description="Название модуля")
    module_goal: str = Field(..., description="Цель модуля")
    lessons: List[Lesson] = Field(default_factory=list, description="Уроки модуля")


class Course(BaseModel):
    """Структура курса"""
    course_title: str = Field(..., description="Название курса")
    course_goals: Optional[str] = Field(default=None, description="Цели курса")
    target_audience: str = Field(..., description="Целевая аудитория")
    duration_hours: Optional[int] = Field(default=None, ge=1)
    duration_weeks: Optional[int] = Field(default=None, ge=1)
    modules: List[Module] = Field(default_factory=list, description="Модули курса")
    
    # Метаданные
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============================================================================
# МОДЕЛИ ДЛЯ ИНТЕРВЬЮ ПО СТРУКТУРЕ КУРСА
# ============================================================================

class CourseBriefStartRequest(BaseModel):
    """Запрос на запуск интервью по теме будущего курса.

    Pre-brief поля задают параметры скрытого черновика (нода A).
    """

    topic: str = Field(..., min_length=3, max_length=200, description="Тема будущего курса")
    course_goals: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=1000,
        description="Цель курса для генерации черновика",
    )
    audience_level: Optional[DifficultyLevel] = Field(
        default=None,
        description="Целевой уровень аудитории курса",
    )
    module_count: Optional[int] = Field(
        default=None,
        ge=2,
        le=12,
        description="Желаемое число разделов в черновике",
    )
    duration_weeks: Optional[int] = Field(
        default=None,
        ge=1,
        le=52,
        description="Длительность курса в неделях",
    )
    hours_per_week: Optional[int] = Field(
        default=None,
        ge=1,
        le=40,
        description="Часов в неделю",
    )


class CourseBriefAnswerRequest(BaseModel):
    """Структурированный ответ пользователя на вопрос о разделе."""
    expected_revision: int = Field(
        ...,
        ge=1,
        description="Версия сессии, для которой сформирован ответ",
    )
    depth: Optional[CourseBriefDepth] = Field(
        default=None,
        description="Нужная глубина проработки раздела; для текстового уточнения не обязательна",
    )
    knowledge_level: Optional[DifficultyLevel] = Field(
        default=None,
        description="Текущий уровень пользователя в этом разделе",
    )
    comment: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Необязательное уточнение пользователя",
    )

    @model_validator(mode="after")
    def requires_substantive_answer(self):
        """Не принимает пустую отправку, но разрешает текстовый follow-up."""
        if self.depth is None and self.knowledge_level is None and not (self.comment or "").strip():
            raise ValueError(
                "Укажите глубину, уровень знаний или добавьте текстовое уточнение."
            )
        return self


class CourseBriefQuestion(BaseModel):
    """Текущий вопрос интервью, не раскрывающий полный черновик структуры."""
    number: int = Field(..., ge=1, description="Номер вопроса")
    total: int = Field(..., ge=1, description="Всего вопросов в интервью")
    text: str = Field(..., description="Текст вопроса")
    kind: CourseBriefQuestionKind = Field(
        default=CourseBriefQuestionKind.MODULE,
        description="Вопрос по модулю, уточнение, новая цель или запрос нового раздела",
    )
    answer_controls: CourseBriefAnswerControls = Field(
        default=CourseBriefAnswerControls.MODULE_GATE,
        description="Какой UI ответа показать: gate-кнопки, шкала уровня/глубины или только текст",
    )


class CourseBriefChatMessage(BaseModel):
    """Сообщение истории интервью для восстановления UI."""

    role: str = Field(..., description="user или assistant")
    content: str = Field(..., description="Текст сообщения")
    sequence: int = Field(..., ge=1, description="Порядок сообщения в сессии")


class CourseBriefProgress(BaseModel):
    """Детерминированный прогресс интервью по разделам курса."""
    completed_questions: int = Field(..., ge=0)
    total_questions: int = Field(..., ge=0)
    percentage: int = Field(..., ge=0, le=100)
    remaining_questions: int = Field(..., ge=0)


class CourseBriefConfidence(BaseModel):
    """Детерминированная полнота собранных требований, не оценка знаний человека."""

    current_module_percentage: int = Field(..., ge=0, le=100)
    structure_percentage: int = Field(..., ge=0, le=100)
    current_module_status: str = Field(..., min_length=1, max_length=32)
    confirmed_signals: int = Field(..., ge=0, le=5)
    total_signals: int = Field(default=5, ge=5, le=5)


class CourseBriefResponse(BaseModel):
    """Состояние сессии интервью, которое безопасно отдавать клиенту."""
    session_id: str
    topic: str
    status: CourseBriefStatus
    revision: int = Field(default=1, ge=1)
    progress: CourseBriefProgress
    confidence: CourseBriefConfidence
    question: Optional[CourseBriefQuestion] = None
    final_course: Optional[Course] = None
    messages: List["CourseBriefChatMessage"] = Field(
        default_factory=list,
        description="История диалога для восстановления чата без дублей",
    )

# ============================================================================
# МОДЕЛИ ДЛЯ ЛЕКЦИЙ И СЛАЙДОВ
# ============================================================================

class Slide(BaseModel):
    """Слайд лекции"""
    slide_number: int = Field(..., ge=1, description="Номер слайда")
    title: str = Field(..., description="Заголовок слайда")
    content: str = Field(..., description="Основной текст слайда")
    slide_type: Union[SlideType, str] = Field(default=SlideType.CONTENT)
    code_example: Optional[str] = Field(default=None, description="Пример кода")
    notes: Optional[str] = Field(default=None, description="Заметки для преподавателя")


class Lecture(BaseModel):
    """Лекция по модулю"""
    lecture_title: str = Field(..., description="Название лекции")
    module_number: int = Field(..., ge=1)
    module_title: str
    duration_minutes: int = Field(default=45, ge=15, le=240)
    slides: List[Slide] = Field(default_factory=list, description="Слайды лекции")
    learning_objectives: List[str] = Field(default_factory=list, description="Цели обучения")
    key_takeaways: List[str] = Field(default_factory=list, description="Ключевые выводы")


class ModuleContent(BaseModel):
    """Полный контент модуля (лекции со слайдами)"""
    module_number: int = Field(..., ge=1)
    module_title: str
    lectures: List[Lecture] = Field(default_factory=list)
    total_slides: int = Field(default=0)
    estimated_duration_minutes: int = Field(default=0)


class GeneratedLecture(BaseModel):
    """Лекция без полей модуля — форма, которую возвращает ИИ для одного урока."""
    lecture_title: str
    duration_minutes: int = Field(default=45, ge=15, le=240)
    slides: List[Slide] = Field(default_factory=list)
    learning_objectives: List[str] = Field(default_factory=list)
    key_takeaways: List[str] = Field(default_factory=list)


class LessonContentUpdate(BaseModel):
    """Тело запроса на обновление контента урока (слайды, лекция)."""
    lecture_title: str = Field(..., description="Название лекции")
    duration_minutes: int = Field(default=45, ge=15, le=240, description="Длительность в минутах")
    learning_objectives: List[str] = Field(default_factory=list, description="Цели обучения")
    key_takeaways: List[str] = Field(default_factory=list, description="Ключевые выводы")
    slides: List[Slide] = Field(default_factory=list, description="Слайды урока")


# ============================================================================
# API МОДЕЛИ (для запросов/ответов)
# ============================================================================

class CourseCreateRequest(BaseModel):
    """Запрос на создание курса"""
    topic: str = Field(..., min_length=3, max_length=200, description="Тема курса")
    course_goals: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Цели и задачи курса",
    )
    audience_level: DifficultyLevel = Field(..., description="Уровень аудитории")
    module_count: int = Field(..., ge=2, le=10, description="Количество модулей")
    duration_weeks: Optional[int] = Field(default=8, ge=1, le=52)
    hours_per_week: Optional[int] = Field(default=5, ge=1, le=40)


class CourseResponse(BaseModel):
    """Ответ с информацией о курсе"""
    id: Optional[int] = None
    course: Course
    status: str = "created"
    message: Optional[str] = None


class GenerateContentRequest(BaseModel):
    """Запрос на генерацию контента модуля"""
    module_number: int = Field(..., ge=1)
    custom_requirements: Optional[str] = None


class ErrorResponse(BaseModel):
    """Ответ с ошибкой"""
    error: str
    detail: Optional[str] = None
    status_code: int = 500
