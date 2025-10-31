"""
Утилиты для извлечения и «починки» JSON, возвращаемого моделью.
Выделено из ContentGenerator для повторного использования и тестирования.
"""
import json
import logging
from typing import Optional, Dict, Any


logger = logging.getLogger(__name__)


def extract_json(content: str, expected_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Извлекает JSON из текстового ответа, пытаясь автоматически исправить частые ошибки.

    - Удаляет markdown-блоки ```json ... ```
    - Пытается закрыть обрезанный JSON
    - Применяет набор регулярных правок для типовых ошибок
    """
    try:
        content = content.replace('```json', '').replace('```', '').strip()

        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        if start_idx == -1 or end_idx <= start_idx:
            logger.error("JSON блок не найден в ответе")
            return None

        json_str = content[start_idx:end_idx]

        # Попытка закрыть обрезанный JSON
        if not json_str.rstrip().endswith('}'):
            json_str = _attempt_close_json(json_str)

        # Попытка 1: обычный парсинг
        try:
            parsed = json.loads(json_str)
            if expected_key and expected_key not in parsed:
                logger.warning(f"Ожидаемый ключ '{expected_key}' отсутствует. Ключи: {list(parsed.keys())}")
            return parsed
        except json.JSONDecodeError as e:
            logger.info("json_sanitizer: applying fixes after JSONDecodeError")
            fixed_json = _fix_json_errors(json_str, e)
            try:
                parsed = json.loads(fixed_json)
                if expected_key and expected_key not in parsed:
                    logger.warning(f"Ожидаемый ключ '{expected_key}' отсутствует после фикса. Ключи: {list(parsed.keys())}")
                return parsed
            except json.JSONDecodeError as e2:
                _log_problem_fragment(json_str, fixed_json, e2)
                return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка извлечения JSON: {e}")
        return None


def _attempt_close_json(json_str: str) -> str:
    try:
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')

        quote_count = json_str.count('"') - json_str.count('\\"')
        in_string = (quote_count % 2) == 1
        if in_string:
            json_str += '"'

        json_str = json_str.rstrip()
        if json_str.endswith(','):
            json_str = json_str[:-1]

        if open_brackets > close_brackets:
            json_str += ']' * (open_brackets - close_brackets)
        if open_braces > close_braces:
            json_str += '}' * (open_braces - close_braces)
        return json_str
    except Exception:
        return json_str


def _fix_json_errors(json_str: str, error: json.JSONDecodeError) -> str:
    import re
    # Удаляем запятые перед закрывающими скобками
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)
    # Двойные запятые
    json_str = json_str.replace(',,', ',')
    # Между строками и объектами
    json_str = re.sub(r'"\s*\n\s*"', '",\n        "', json_str)
    json_str = re.sub(r'}\s*\n\s*{', '},\n        {', json_str)
    json_str = re.sub(r'}\s*\n\s*"', '},\n        "', json_str)
    json_str = re.sub(r']\s*\n\s*"', '],\n        "', json_str)
    # Удаляем BOM
    json_str = json_str.replace('\ufeff', '')

    # Локальная вставка запятой по позиции ошибки
    if hasattr(error, 'pos') and error.pos:
        pos = error.pos
        if 0 < pos < len(json_str):
            before = json_str[max(0, pos-5):pos]
            after = json_str[pos:min(len(json_str), pos+5)]
            if before.rstrip().endswith('"') and after.lstrip().startswith('"'):
                json_str = json_str[:pos] + ',' + json_str[pos:]
    return json_str


def _log_problem_fragment(original_json: str, fixed_json: str, error: Exception) -> None:
    try:
        error_pos = getattr(error, 'pos', None)
        if isinstance(error, json.JSONDecodeError):
            error_pos = error.pos
        if error_pos is not None:
            context_start = max(0, error_pos - 100)
            context_end = min(len(original_json), error_pos + 100)
            logger.error(
                f"Проблемная часть JSON (позиция {error_pos}): ...{original_json[context_start:context_end]}..."
            )
    except Exception:
        pass


