"""
Централизованные настройки проекта (env + дефолты).
"""
import os
from dotenv import load_dotenv


load_dotenv()

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_DEFAULT = os.getenv("OPENAI_MODEL_DEFAULT", "gpt-4")
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "120"))
OPENAI_TEMPERATURE_DEFAULT = float(os.getenv("OPENAI_TEMPERATURE_DEFAULT", "0.7"))
OPENAI_MAX_TOKENS_DEFAULT = int(os.getenv("OPENAI_MAX_TOKENS_DEFAULT", "3000"))
OPENAI_RETRIES_DEFAULT = int(os.getenv("OPENAI_RETRIES_DEFAULT", "2"))
OPENAI_BACKOFF_SECONDS_DEFAULT = float(os.getenv("OPENAI_BACKOFF_SECONDS_DEFAULT", "1.0"))
PROMPT_VERSION = os.getenv("PROMPT_VERSION", "v1")
AI_CACHE_ENABLED = (os.getenv("AI_CACHE_ENABLED", "true").lower() in ("1", "true", "yes"))
AI_CACHE_TTL_SECONDS = int(os.getenv("AI_CACHE_TTL_SECONDS", "86400"))

# HeyGen
HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")
HEYGEN_API_URL = os.getenv("HEYGEN_API_URL", "https://api.heygen.com")
HEYGEN_DEFAULT_AVATAR_ID = os.getenv("HEYGEN_DEFAULT_AVATAR_ID", "Abigail_expressive_2024112501")
HEYGEN_DEFAULT_VOICE_ID = os.getenv("HEYGEN_DEFAULT_VOICE_ID", "9799f1ba6acd4b2b993fe813a18f9a91")
HEYGEN_TIMEOUT = int(os.getenv("HEYGEN_TIMEOUT", "30"))
HEYGEN_STATUS_TIMEOUT = int(os.getenv("HEYGEN_STATUS_TIMEOUT", "10"))
HEYGEN_DOWNLOAD_TIMEOUT = int(os.getenv("HEYGEN_DOWNLOAD_TIMEOUT", "60"))
HEYGEN_POLL_INTERVAL_SECONDS = int(os.getenv("HEYGEN_POLL_INTERVAL_SECONDS", "10"))

# Network
HTTPS_PROXY = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")


