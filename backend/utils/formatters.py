"""
Слой совместимости: реэкспорт утилит из специализированных модулей.
Старые импорты backend/utils/formatters.py продолжают работать.
"""
from .strings import safe_filename  # noqa: F401
from .http import encode_filename, format_content_disposition  # noqa: F401

