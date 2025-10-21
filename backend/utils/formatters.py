"""
Утилиты для форматирования данных
"""
from urllib.parse import quote


def safe_filename(text: str, extension: str = None) -> str:
    """
    Создает безопасное имя файла из текста
    
    Args:
        text: Исходный текст
        extension: Расширение файла (опционально)
        
    Returns:
        Безопасное имя файла
    """
    safe_text = text.replace(' ', '_').replace('/', '_').replace('\\', '_')
    
    if extension:
        return f"{safe_text}.{extension}"
    return safe_text


def encode_filename(filename: str) -> str:
    """
    URL-кодирует имя файла для корректной работы с кириллицей
    
    Args:
        filename: Имя файла
        
    Returns:
        URL-кодированное имя файла
    """
    return quote(filename)


def format_content_disposition(filename: str) -> str:
    """
    Форматирует заголовок Content-Disposition для скачивания файла
    
    Args:
        filename: Имя файла
        
    Returns:
        Строка для заголовка Content-Disposition
    """
    encoded = encode_filename(filename)
    return f"attachment; filename*=UTF-8''{encoded}"

