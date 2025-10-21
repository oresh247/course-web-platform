"""
Доменные модели данных (Pydantic)
Адаптировано из TGBotCreateCourse проекта
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Union
from enum import Enum
from datetime import datetime


class DifficultyLevel(str, Enum):
    """Уровень сложности курса"""
    JUNIOR = "junior"
    MIDDLE = "middle"
    SENIOR = "senior"


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


class Module(BaseModel):
    """Модуль курса"""
    module_number: int = Field(..., ge=1, description="Номер модуля")
    module_title: str = Field(..., description="Название модуля")
    module_goal: str = Field(..., description="Цель модуля")
    lessons: List[Lesson] = Field(default_factory=list, description="Уроки модуля")


class Course(BaseModel):
    """Структура курса"""
    course_title: str = Field(..., description="Название курса")
    target_audience: str = Field(..., description="Целевая аудитория")
    duration_hours: Optional[int] = Field(default=None, ge=1)
    duration_weeks: Optional[int] = Field(default=None, ge=1)
    modules: List[Module] = Field(default_factory=list, description="Модули курса")
    
    # Метаданные
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


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


# ============================================================================
# API МОДЕЛИ (для запросов/ответов)
# ============================================================================

class CourseCreateRequest(BaseModel):
    """Запрос на создание курса"""
    topic: str = Field(..., min_length=3, max_length=200, description="Тема курса")
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

