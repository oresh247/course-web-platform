"""
Строковые утилиты: безопасные имена файлов и т.п.
"""


def safe_filename(text: str, extension: str = None) -> str:
    """Создает безопасное имя файла из текста.

    - Пробелы → "_"
    - Слеши и обратные слеши → "_"
    """
    safe_text = text.replace(' ', '_').replace('/', '_').replace('\\', '_')
    if extension:
        return f"{safe_text}.{extension}"
    return safe_text


