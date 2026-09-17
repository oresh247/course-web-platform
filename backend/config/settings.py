"""
Централизованные настройки проекта (env + дефолты).
"""
import os
from pathlib import Path
from dotenv import load_dotenv


# Основное место для секретов backend — ``backend/.env``. Явно загружаем его,
# чтобы запуск из корня репозитория (``uvicorn backend.main:app``) и запуск из
# каталога backend вели себя одинаково. Переменные уже заданные в окружении не
# перезаписываются.
BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")
load_dotenv()

# OpenAI (используется, если OPENROUTER_API_KEY не задан)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# OpenRouter (https://openrouter.ai/) — единый API для разных моделей
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = (
    os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()
    or "https://openrouter.ai/api/v1"
)

# Определение провайдера: если задан OPENROUTER_API_KEY — используем OpenRouter, иначе OpenAI
USE_OPENROUTER = bool((OPENROUTER_API_KEY or "").strip())

OPENAI_MODEL_DEFAULT = os.getenv("OPENAI_MODEL_DEFAULT", "gpt-4").strip() or "gpt-4"
OPENAI_MODEL_DETAILED_CONTENT = os.getenv("OPENAI_MODEL_DETAILED_CONTENT", "gpt-4-turbo-preview")
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "120"))
OPENAI_TEMPERATURE_DEFAULT = float(os.getenv("OPENAI_TEMPERATURE_DEFAULT", "0.7"))
# Максимальные токены для разных типов генерации
OPENAI_MAX_TOKENS_DEFAULT = int(os.getenv("OPENAI_MAX_TOKENS_DEFAULT", "3000"))
# Генерация структуры курса (большой JSON): 12000 чтобы ответ не обрезался (для очень больших курсов — 16000)
OPENAI_MAX_TOKENS_COURSE_STRUCTURE = int(os.getenv("OPENAI_MAX_TOKENS_COURSE_STRUCTURE", "12000"))
OPENAI_MAX_TOKENS_MODULE_CONTENT = int(os.getenv("OPENAI_MAX_TOKENS_MODULE_CONTENT", "4096"))
OPENAI_MAX_TOKENS_LESSON_DETAILED = int(os.getenv("OPENAI_MAX_TOKENS_LESSON_DETAILED", "12000"))
OPENAI_MAX_TOKENS_TOPIC_MATERIAL = int(os.getenv("OPENAI_MAX_TOKENS_TOPIC_MATERIAL", "4096"))
OPENAI_MAX_TOKENS_SHORT_MIN = int(os.getenv("OPENAI_MAX_TOKENS_SHORT_MIN", "200"))
OPENAI_MAX_TOKENS_SHORT_MAX = int(os.getenv("OPENAI_MAX_TOKENS_SHORT_MAX", "500"))
# Настройки для генерации тестов
# Используем модель, которая поддерживает JSON mode (gpt-4-turbo-preview, gpt-4o, gpt-3.5-turbo)
OPENAI_MODEL_TEST = os.getenv("OPENAI_MODEL_TEST", "gpt-4-turbo-preview")
OPENAI_TEMPERATURE_TEST = float(os.getenv("OPENAI_TEMPERATURE_TEST", "0.7"))
OPENAI_MAX_TOKENS_TEST = int(os.getenv("OPENAI_MAX_TOKENS_TEST", "3000"))
OPENAI_RETRIES_DEFAULT = int(os.getenv("OPENAI_RETRIES_DEFAULT", "2"))
OPENAI_BACKOFF_SECONDS_DEFAULT = float(os.getenv("OPENAI_BACKOFF_SECONDS_DEFAULT", "1.0"))
PROMPT_VERSION = os.getenv("PROMPT_VERSION", "v1")
AI_CACHE_ENABLED = (os.getenv("AI_CACHE_ENABLED", "true").lower() in ("1", "true", "yes"))
AI_CACHE_TTL_SECONDS = int(os.getenv("AI_CACHE_TTL_SECONDS", "86400"))

# Локальный demo-режим только для интервью по структуре курса. В нём
# CourseBriefService использует детерминированный клиент вместо внешней модели.
COURSE_BRIEF_DEMO_MODE = (
    os.getenv("COURSE_BRIEF_DEMO_MODE", "false").strip().lower()
    in ("1", "true", "yes")
)

# Настройки модели, которая интерпретирует один ответ в интервью по структуре
# курса. Модель можно менять независимо от модели финальной генерации курса.
# Пустое значение намеренно означает «использовать общую модель по умолчанию».
COURSE_BRIEF_INTERVIEW_MODEL = (
    os.getenv("COURSE_BRIEF_INTERVIEW_MODEL", "").strip()
    or OPENAI_MODEL_DEFAULT
)
COURSE_BRIEF_INTERVIEW_TEMPERATURE = float(
    os.getenv("COURSE_BRIEF_INTERVIEW_TEMPERATURE", "0.2")
)
COURSE_BRIEF_INTERVIEW_MAX_TOKENS = int(
    os.getenv("COURSE_BRIEF_INTERVIEW_MAX_TOKENS", "1200")
)

# HeyGen
HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")
HEYGEN_API_URL = os.getenv("HEYGEN_API_URL", "https://api.heygen.com")
HEYGEN_DEFAULT_AVATAR_ID = os.getenv("HEYGEN_DEFAULT_AVATAR_ID", "Abigail_expressive_2024112501")
# Голос по умолчанию должен поддерживать язык озвучки (например ru).
# Иначе HeyGen вернёт VOICE_CLIENT_ERROR. Список голосов: GET /v2/voices, выбрать voice_id с language "ru".
HEYGEN_DEFAULT_VOICE_ID = os.getenv("HEYGEN_DEFAULT_VOICE_ID", "9799f1ba6acd4b2b993fe813a18f9a91")
HEYGEN_TIMEOUT = int(os.getenv("HEYGEN_TIMEOUT", "30"))
HEYGEN_STATUS_TIMEOUT = int(os.getenv("HEYGEN_STATUS_TIMEOUT", "10"))
HEYGEN_DOWNLOAD_TIMEOUT = int(os.getenv("HEYGEN_DOWNLOAD_TIMEOUT", "60"))
HEYGEN_POLL_INTERVAL_SECONDS = int(os.getenv("HEYGEN_POLL_INTERVAL_SECONDS", "10"))

# Network
HTTPS_PROXY = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
