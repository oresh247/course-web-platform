"""
Трансформации данных: сборка payload и нормализация ответов HeyGen.
"""
from typing import Dict, Any, Optional


def build_create_video_payload(
    *,
    text: str,
    avatar_id: str,
    voice_id: str,
    language: str,
    background_id: Optional[str],
    quality: str,
    test_mode: bool,
) -> Dict[str, Any]:
    return {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": avatar_id,
                    "avatar_style": "normal",
                },
                "voice": {
                    "type": "text",
                    "input_text": text,
                    "voice_id": voice_id,
                    "language": language,
                },
                "background": (
                    {"type": "color", "value": "#ffffff"}
                    if not background_id
                    else {"type": "image", "value": background_id}
                ),
            }
        ],
        "dimension": {
            "width": 1920 if quality == "high" else 1280,
            "height": 1080 if quality == "high" else 720,
        },
        "aspect_ratio": "16:9",
        "quality": quality,
        "test": test_mode,
    }


def normalize_create_video_response(result: Dict[str, Any]) -> Dict[str, Any]:
    video_id = None
    if result.get("data") and isinstance(result.get("data"), dict):
        video_id = result.get("data", {}).get("video_id")
    if not video_id:
        video_id = result.get("video_id")
    if not video_id:
        error_message = result.get("message", "Неизвестная ошибка генерации")
        error_code = result.get("code", "unknown")
        raise Exception(f"HeyGen generation failed: {error_message} (code: {error_code})")
    return {
        "video_id": video_id,
        "script": (result.get("data", {}) or {}).get("script", ""),
        "created_at": (result.get("data", {}) or {}).get("created_at", ""),
        "status": (result.get("data", {}) or {}).get("status", "generating"),
    }


