"""
Сервис для AI-генерации контента (регенерация целей, планов контента)
"""
import logging
from typing import Optional, Dict, Any, List

from backend.ai.openai_client import OpenAIClient
from backend.ai.interfaces import AIChatClient

logger = logging.getLogger(__name__)


class GenerationService:
    """Сервис для AI-генерации и регенерации контента"""
    
    def __init__(self, ai_client: AIChatClient | None = None):
        self.openai_client: AIChatClient = ai_client or OpenAIClient()
    
    def regenerate_module_goal(
        self,
        course_title: str,
        target_audience: str,
        module_number: int,
        module_title: str
    ) -> Optional[str]:
        """Регенерирует цель модуля с помощью AI"""
        try:
            prompt = f"""Курс: {course_title}
Целевая аудитория: {target_audience}
Модуль {module_number}: {module_title}

Сгенерируй краткую (1-2 предложения) и четкую цель для этого модуля.
Ответь ТОЛЬКО целью, без дополнительного текста."""
            
            new_goal = self.openai_client.call_ai(
                system_prompt="Ты эксперт по созданию образовательного контента.",
                user_prompt=prompt,
                model="gpt-4",
                temperature=0.7,
                max_tokens=200
            )
            logger.info(f"✅ Цель модуля регенерирована: {new_goal[:50]}...")
            return new_goal
            
        except Exception as e:
            logger.error(f"Ошибка регенерации цели модуля: {e}")
            return None
    
    def regenerate_lesson_content_outline(
        self,
        course_title: str,
        module_title: str,
        lesson_title: str,
        lesson_goal: str,
        lesson_format: str,
        estimated_time_minutes: int
    ) -> Optional[List[str]]:
        """Регенерирует план контента урока с помощью AI"""
        try:
            prompt = f"""Курс: {course_title}
Модуль: {module_title}
Урок: {lesson_title}
Цель урока: {lesson_goal}
Формат: {lesson_format}
Время: {estimated_time_minutes} минут

Сгенерируй детальный план контента для этого урока (5-7 пунктов).
Верни ТОЛЬКО список пунктов, каждый с новой строки, начиная с "- "."""
            
            content_text = self.openai_client.call_ai(
                system_prompt="Ты эксперт по созданию образовательного контента.",
                user_prompt=prompt,
                model="gpt-4",
                temperature=0.7,
                max_tokens=500
            )
            
            # Парсим ответ в список
            new_content_outline = []
            for line in content_text.split('\n'):
                line = line.strip()
                if line.startswith('- '):
                    new_content_outline.append(line[2:])
                elif line.startswith('* '):
                    new_content_outline.append(line[2:])
                elif line and not line.startswith('#'):
                    new_content_outline.append(line)
            
            if not new_content_outline:
                new_content_outline = [content_text]
            
            logger.info(f"✅ План контента регенерирован: {len(new_content_outline)} пунктов")
            return new_content_outline
            
        except Exception as e:
            logger.error(f"Ошибка регенерации плана контента: {e}")
            return None


# Глобальный экземпляр
generation_service = GenerationService()

