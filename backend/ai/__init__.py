"""AI модуль для генерации контента курсов"""
from .openai_client import OpenAIClient
from .content_generator import ContentGenerator
from . import prompts

__all__ = ['OpenAIClient', 'ContentGenerator', 'prompts']

