"""
Интерфейсы (порты) AI-уровня для ослабления связности и тестирования.
"""
from typing import Optional, Dict, Any, Protocol


class AIChatClient(Protocol):
    def call_ai(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 3000,
        response_format: Optional[Dict[str, str]] = None,
        retries: int = 2,
        backoff_seconds: float = 1.0,
    ) -> Optional[str]:
        ...

    def call_ai_json(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 3000,
        retries: int = 2,
        backoff_seconds: float = 1.0,
    ) -> Optional[Dict[str, Any]]:
        ...


