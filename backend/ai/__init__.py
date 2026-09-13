"""AI модуль для генерации контента курсов.

Тяжёлые клиенты загружаются лениво: это позволяет использовать промпты и
сервисы с подставным клиентом в тестах без обязательной установки SDK OpenAI.
"""
from . import prompts

__all__ = ['OpenAIClient', 'ContentGenerator', 'prompts']


def __getattr__(name):
    """Лениво отдаёт AI-классы, сохраняя прежний публичный импорт."""
    if name == 'OpenAIClient':
        from .openai_client import OpenAIClient
        return OpenAIClient
    if name == 'ContentGenerator':
        from .content_generator import ContentGenerator
        return ContentGenerator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
