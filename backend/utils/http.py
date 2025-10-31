"""
HTTP‑утилиты: формирование заголовков скачивания и кодирование имён файлов.

Используемая библиотека:
- `urllib.parse.quote` — стандартная функция Python для URL‑кодирования,
  нужна, чтобы корректно отдавать файлы с кириллицей в имени.
"""
from urllib.parse import quote


def encode_filename(filename: str) -> str:
    """URL-кодирует имя файла (поддержка кириллицы)."""
    return quote(filename)


def format_content_disposition(filename: str) -> str:
    """Формирует заголовок Content-Disposition для скачивания файла."""
    encoded = encode_filename(filename)
    return f"attachment; filename*=UTF-8''{encoded}"


