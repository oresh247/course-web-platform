"""Детерминированный AI-клиент для локальной проверки Course Brief MVP.

Этот клиент намеренно доступен только при COURSE_BRIEF_DEMO_MODE=true. Он не
делает сетевых запросов и позволяет проверить пользовательский сценарий без
ключа OpenAI или OpenRouter.
"""
from typing import Any, Dict, Optional


class CourseBriefDemoClient:
    """Возвращает валидный черновик курса для локального demo-режима."""

    def generate_course_structure(
        self,
        topic: str,
        audience_level: str,
        module_count: int,
        course_goals: Optional[str] = None,
        duration_weeks: Optional[int] = None,
        hours_per_week: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Создаёт минимальную, но реалистичную структуру.

        Внешняя модель при этом не вызывается.
        """
        modules = []
        module_titles = (
            "Контекст и базовые понятия",
            "Ключевые практики",
            "Рабочие сценарии",
            "Закрепление и следующий шаг",
        )
        for module_number in range(1, module_count + 1):
            title = module_titles[(module_number - 1) % len(module_titles)]
            intro_lesson_title = f"Основы раздела {module_number}"
            practice_lesson_title = f"Практика раздела {module_number}"
            intro_lesson_goal = "Разобраться с ключевыми понятиями."
            practice_lesson_goal = "Применить материал в рабочем сценарии."
            modules.append(
                {
                    "module_number": module_number,
                    "module_title": f"{title}: {topic}",
                    "module_goal": (
                        f"Сформировать основу по теме «{topic}» "
                        f"в разделе {module_number}."
                    ),
                    "lessons": [
                        {
                            "lesson_title": intro_lesson_title,
                            "lesson_goal": intro_lesson_goal,
                            "content_outline": [
                                "Контекст",
                                "Термины",
                                "Пример",
                            ],
                            "assessment": "Короткая практика",
                            "format": "theory",
                            "estimated_time_minutes": 30,
                        },
                        {
                            "lesson_title": practice_lesson_title,
                            "lesson_goal": practice_lesson_goal,
                            "content_outline": [
                                "Задание",
                                "Разбор",
                                "Самопроверка",
                            ],
                            "assessment": "Практическое " "задание",
                            "format": "practice",
                            "estimated_time_minutes": 45,
                        },
                    ],
                }
            )

        return {
            "course_title": f"{topic}: локальный демо-курс",
            "course_goals": course_goals
            or "Проверить сценарий уточнения " "структуры курса.",
            "target_audience": audience_level,
            "duration_hours": max(module_count * 2, 1),
            "duration_weeks": duration_weeks or 1,
            "modules": modules,
        }

    def call_ai_json(self, **_: Any) -> None:
        """Включает существующий детерминированный fallback финализации."""
        return None
