"""
Порты (Protocol) для HeyGen-клиента, чтобы ослабить связность и упростить тестирование.
"""
from typing import Protocol, Dict, Any, Optional


class HeygenClient(Protocol):
    def create_video_from_text(
        self,
        text: str,
        avatar_id: str,
        voice_id: str,
        background_id: Optional[str] = None,
        language: str = "ru",
        quality: str = "low",
        test_mode: bool = False,
    ) -> Dict[str, Any]:
        ...

    def get_video_status(self, video_id: str) -> Dict[str, Any]:
        ...

    def download_video(self, video_id: str, output_path: str) -> bool:
        ...

    def get_available_avatars(self) -> Dict[str, Any]:
        ...

    def get_available_voices(self) -> Dict[str, Any]:
        ...

    def wait_for_video_completion(self, video_id: str, max_wait_time: int = 300) -> Dict[str, Any]:
        ...

    def create_lesson_video(
        self,
        lesson_title: str,
        lesson_content: str,
        avatar_id: str,
        voice_id: str,
    ) -> Dict[str, Any]:
        ...

    def get_video_download_url(self, video_id: str) -> Optional[str]:
        ...


