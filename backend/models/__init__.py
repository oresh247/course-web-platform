"""Модели данных"""
from .domain import (
    Course, Module, Lesson, LessonContent, TopicMaterial,
    Lecture, Slide, ModuleContent,
    DifficultyLevel, LessonFormat, SlideType,
    CourseCreateRequest, CourseResponse, GenerateContentRequest, ErrorResponse
)

__all__ = [
    'Course', 'Module', 'Lesson', 'LessonContent', 'TopicMaterial',
    'Lecture', 'Slide', 'ModuleContent',
    'DifficultyLevel', 'LessonFormat', 'SlideType',
    'CourseCreateRequest', 'CourseResponse', 'GenerateContentRequest', 'ErrorResponse'
]

