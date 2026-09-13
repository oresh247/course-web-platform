r"""Небольшая автономная проверка JSON-fallback без сети и ключей.

Запуск из корня репозитория:
    .\.venv\Scripts\python.exe .\backend\tools\test_openai_client_json_fallback.py
"""
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.ai.openai_client import OpenAIClient


class ScriptedCall:
    """Подменяет ``call_ai`` и фиксирует варианты response_format."""

    def __init__(self, responses: List[Optional[str]]):
        self._responses = list(responses)
        self.calls: List[Dict[str, Any]] = []

    def __call__(self, **kwargs: Any) -> Optional[str]:
        self.calls.append(kwargs)
        return self._responses.pop(0)


def make_client(responses: List[Optional[str]], use_openrouter: bool) -> tuple[OpenAIClient, ScriptedCall]:
    """Создаёт объект без ``__init__``, поэтому SDK и сеть не используются."""
    client = OpenAIClient.__new__(OpenAIClient)
    client._use_openrouter = use_openrouter
    scripted_call = ScriptedCall(responses)
    client.call_ai = scripted_call  # type: ignore[method-assign]
    return client, scripted_call


def test_schema_rejection_falls_back_to_plain_json() -> None:
    client, scripted_call = make_client(
        [None, None, '{"action":"ask"}'],
        use_openrouter=True,
    )

    result = client.call_ai_json(
        system_prompt="system",
        user_prompt="user",
        model="provider/model",
        json_schema={
            "name": "course_brief_interview",
            "schema": {"type": "object", "properties": {}},
            "strict": True,
        },
    )

    assert result == {"action": "ask"}
    assert len(scripted_call.calls) == 3
    assert scripted_call.calls[0]["response_format"] == {
        "type": "json_schema",
        "json_schema": {
            "name": "course_brief_interview",
            "schema": {"type": "object", "properties": {}},
            "strict": True,
        },
    }
    assert scripted_call.calls[0]["retries"] == 0
    assert scripted_call.calls[1]["response_format"] == {"type": "json_object"}
    assert scripted_call.calls[1]["retries"] == 0
    assert scripted_call.calls[2]["response_format"] is None


def test_raw_schema_is_strict_by_default() -> None:
    client, scripted_call = make_client(['{"ok":true}'], use_openrouter=True)

    result = client.call_ai_json(
        system_prompt="system",
        user_prompt="user",
        model="provider/model",
        json_schema={"type": "object", "properties": {"ok": {"type": "boolean"}}},
    )

    assert result == {"ok": True}
    assert len(scripted_call.calls) == 1
    response_format = scripted_call.calls[0]["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["name"] == "structured_response"
    assert response_format["json_schema"]["strict"] is True


def test_extract_message_prefers_content_over_reasoning() -> None:
    class _Message:
        content = '{"ok":true}'
        reasoning = '{"ok":false}'

    assert OpenAIClient._extract_message_text(_Message()) == '{"ok":true}'


def test_extract_message_uses_reasoning_when_content_empty() -> None:
    class _Message:
        content = None
        reasoning = '{"ok":true}'

    assert OpenAIClient._extract_message_text(_Message()) == '{"ok":true}'


def test_extract_message_reads_list_content() -> None:
    class _Message:
        content = [{"type": "text", "text": '{"ok":true}'}]
        reasoning = None

    assert OpenAIClient._extract_message_text(_Message()) == '{"ok":true}'


def test_unknown_non_json_model_uses_plain_call() -> None:
    client, scripted_call = make_client(['{"ok":true}'], use_openrouter=False)

    result = client.call_ai_json(
        system_prompt="system",
        user_prompt="user",
        model="provider/no-json-mode",
    )

    assert result == {"ok": True}
    assert len(scripted_call.calls) == 1
    assert scripted_call.calls[0]["response_format"] is None


def main() -> None:
    test_schema_rejection_falls_back_to_plain_json()
    test_raw_schema_is_strict_by_default()
    test_extract_message_prefers_content_over_reasoning()
    test_extract_message_uses_reasoning_when_content_empty()
    test_extract_message_reads_list_content()
    test_unknown_non_json_model_uses_plain_call()
    print("OK: json_schema, json_object и plain fallback проверены без сети")


if __name__ == "__main__":
    main()
