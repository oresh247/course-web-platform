"""
Сервис для генерации тестов для уроков с использованием AI
"""
import logging
from typing import Optional, Dict, Any

from backend.ai.openai_client import OpenAIClient
from backend.ai.interfaces import AIChatClient
from backend.ai.json_sanitizer import extract_json
from backend.ai.prompts import (
    TEST_GENERATION_SYSTEM_PROMPT,
    TEST_GENERATION_PROMPT_TEMPLATE,
    format_content_outline
)
from backend.models.domain import LessonTest
from backend.config import settings

logger = logging.getLogger(__name__)


class TestGeneratorService:
    """Сервис для генерации тестов для уроков"""
    
    def __init__(self, ai_client: AIChatClient | None = None):
        self.openai_client: AIChatClient = ai_client or OpenAIClient()
    
    def generate_test(
        self,
        lesson_title: str,
        lesson_goal: str,
        content_outline: list[str],
        course_title: str,
        target_audience: str,
        module_title: str,
        num_questions: int = 10,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None
    ) -> Optional[LessonTest]:
        """
        Генерирует тест для урока с использованием AI
        
        Args:
            lesson_title: Название урока
            lesson_goal: Цель урока
            content_outline: План контента урока
            course_title: Название курса
            target_audience: Целевая аудитория
            module_title: Название модуля
            num_questions: Количество вопросов (по умолчанию 10)
            model: Модель AI (если None, используется настройка по умолчанию)
            temperature: Температура для генерации (если None, используется настройка по умолчанию)
            max_tokens: Максимальное количество токенов (если None, используется настройка по умолчанию)
            
        Returns:
            LessonTest объект или None при ошибке
        """
        logger.info(f"Генерируем тест для урока: {lesson_title}")
        
        try:
            # Используем настройки по умолчанию, если не указаны
            if model is None:
                model = getattr(settings, 'OPENAI_MODEL_TEST', settings.OPENAI_MODEL_DEFAULT)
            if temperature is None:
                temperature = getattr(settings, 'OPENAI_TEMPERATURE_TEST', settings.OPENAI_TEMPERATURE_DEFAULT)
            if max_tokens is None:
                max_tokens = getattr(settings, 'OPENAI_MAX_TOKENS_TEST', settings.OPENAI_MAX_TOKENS_DEFAULT)
            
            prompt = TEST_GENERATION_PROMPT_TEMPLATE.format(
                course_title=course_title,
                target_audience=target_audience,
                module_title=module_title,
                lesson_title=lesson_title,
                lesson_goal=lesson_goal,
                content_outline=format_content_outline(content_outline),
                num_questions=num_questions
            )
            
            # Генерируем тест через AI
            content_json = self.openai_client.call_ai_json(
                system_prompt=TEST_GENERATION_SYSTEM_PROMPT,
                user_prompt=prompt,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if not content_json:
                logger.warning("❌ AI не вернул результат для теста")
                return None
            
            # Валидация через Pydantic
            try:
                test = LessonTest(**content_json)
                # Убеждаемся, что total_questions соответствует количеству вопросов
                test.total_questions = len(test.questions)
                logger.info(f"✅ Тест успешно сгенерирован: {test.total_questions} вопросов")
                return test
            except Exception as e:
                logger.error(f"❌ Ошибка валидации теста: {e}")
                logger.debug(f"Проблемный JSON: {content_json}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка генерации теста: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None

