"""
Простой HTTP‑клиент для HeyGen API.

Для сетевых вызовов используется библиотека `requests` — она удобна для
выполнения HTTP запросов (GET/POST/stream) и обработки ответов.

Особенности корпоративных сетей:
- Встречаются самоподписанные сертификаты. Мы отключаем строгую проверку SSL
  (через `ssl` и переменные окружения), чтобы не падать на валидации сертификатов.
  Делайте это только для отладки. В проде используйте корректные сертификаты.
"""
import os
import requests
import logging
import ssl
from typing import Dict, Any, Optional


logger = logging.getLogger(__name__)


class HeygenHttpClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("HEYGEN_API_KEY")
        self.base_url = base_url or os.getenv("HEYGEN_API_URL", "https://api.heygen.com")
        if not self.api_key:
            raise ValueError("HEYGEN_API_KEY не найден в переменных окружения")

        # SSL fix для корпоративных сетей
        os.environ["PYTHONHTTPSVERIFY"] = "0"
        os.environ["CURL_CA_BUNDLE"] = ""
        os.environ["REQUESTS_CA_BUNDLE"] = ""
        ssl._create_default_https_context = ssl._create_unverified_context

        self.headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json",
        }

    def post(self, path: str, json_payload: Dict[str, Any], timeout: int = 30) -> requests.Response:
        """Выполняет POST запрос к HeyGen API.

        Args:
            path: относительный путь (например, "/v2/video/generate").
            json_payload: тело запроса в формате dict — `requests` сам сериализует в JSON.
            timeout: таймаут в секундах на ожидание ответа.

        Returns:
            Объект `requests.Response` со статусом и телом ответа.
        """
        url = f"{self.base_url}{path}"
        return requests.post(url, headers=self.headers, json=json_payload, timeout=timeout, verify=False)

    def get(self, path: str, timeout: int = 10) -> requests.Response:
        """Выполняет GET запрос к HeyGen API.

        Args:
            path: относительный путь.
            timeout: таймаут в секундах на ожидание ответа.

        Returns:
            `requests.Response`.
        """
        url = f"{self.base_url}{path}"
        return requests.get(url, headers=self.headers, timeout=timeout, verify=False)

    def stream(self, path: str, timeout: int = 60) -> requests.Response:
        """Выполняет потоковую загрузку (stream) — например, скачивание видео.

        Args:
            path: относительный путь.
            timeout: таймаут в секундах.

        Returns:
            `requests.Response` с `stream=True`.
        """
        url = f"{self.base_url}{path}"
        return requests.get(url, headers=self.headers, stream=True, timeout=timeout, verify=False)


