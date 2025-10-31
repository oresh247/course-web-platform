"""
Тестовый скрипт проверки доступа к HeyGen и открытия видео по video_id.

Запуск (из корня проекта или каталога backend):
  python backend/check_heygen_access.py --video 08317e57b38e4ef4a9134b06130fa14d

Параметры окружения:
  HEYGEN_API_KEY        - API ключ HeyGen (обязательно для прямого доступа)
  HEYGEN_API_URL        - Базовый URL (по умолчанию https://api.heygen.com)
  HTTPS_PROXY / HTTP_PROXY - при необходимости корпоративного прокси

Опционально можно проверять через ваш бэкенд (если он уже поднят):
  python backend/check_heygen_access.py --video <id> --backend http://localhost:8000
"""

import os
import sys
import json
import argparse
import requests
from typing import Optional
from dotenv import load_dotenv


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    return v if v is not None else default


def build_session() -> requests.Session:
    s = requests.Session()
    # Часто в корпоративной сети требуется отключить verify (у вас уже так делается в клиенте)
    s.verify = False  # ЗНАЧЕНИЕ ТОЛЬКО ДЛЯ ОТЛАДКИ
    # Проксирование берётся из переменных окружения автоматически (HTTPS_PROXY/HTTP_PROXY)
    return s


def check_avatars(session: requests.Session, base_url: str, api_key: str) -> None:
    url = base_url.rstrip("/") + "/v2/avatars"
    r = session.get(url, headers={"X-Api-Key": api_key, "Content-Type": "application/json"}, timeout=20)
    r.raise_for_status()
    data = r.json()
    total = len(data.get("data", [])) if isinstance(data, dict) else None
    print(f"[OK] Avatars: HTTP {r.status_code}, count={total}")


def check_status(session: requests.Session, base_url: str, api_key: str, video_id: str) -> dict:
    url = base_url.rstrip("/") + "/v1/video_status.get"
    r = session.get(url, params={"video_id": video_id}, headers={"X-Api-Key": api_key}, timeout=30)
    r.raise_for_status()
    data = r.json()
    print(f"[OK] Status: HTTP {r.status_code}, body keys={list(data.keys())}")
    return data


def try_download_small_chunk(session: requests.Session, base_url: str, api_key: str, video_id: str) -> None:
    url = base_url.rstrip("/") + "/v1/video.download"
    with session.get(url, params={"video_id": video_id}, headers={"X-Api-Key": api_key}, stream=True, timeout=60) as r:
        r.raise_for_status()
        # Считываем небольшой кусочек для проверки доступности
        chunk = next(r.iter_content(chunk_size=1024), b"")
        print(f"[OK] Download stream: HTTP {r.status_code}, first_chunk={len(chunk)} bytes")


def check_via_backend(session: requests.Session, backend_url: str, video_id: str) -> None:
    status_url = backend_url.rstrip("/") + f"/api/video/status/{video_id}"
    r = session.get(status_url, timeout=20)
    r.raise_for_status()
    data = r.json()
    download_url = (data or {}).get("data", {}).get("download_url")
    print(f"[OK] Backend status: HTTP {r.status_code}, download_url={download_url}")
    if download_url:
        with session.get(download_url, stream=True, timeout=60) as dr:
            dr.raise_for_status()
            chunk = next(dr.iter_content(chunk_size=1024), b"")
            print(f"[OK] Backend download: HTTP {dr.status_code}, first_chunk={len(chunk)} bytes")


def main() -> int:
    # Загружаем переменные окружения из backend/.env, даже если запускаем из корня
    try:
        here = os.path.dirname(__file__)
        env_path = os.path.join(here, ".env")
        load_dotenv(env_path)
        # Также пробуем корневой .env как запасной вариант
        load_dotenv(os.path.join(os.path.dirname(here), ".env"))
    except Exception:
        pass
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, help="video_id для проверки")
    parser.add_argument("--backend", help="URL вашего бэкенда (например http://localhost:8000)")
    args = parser.parse_args()

    api_key = get_env("HEYGEN_API_KEY")
    base_url = get_env("HEYGEN_API_URL", "https://api.heygen.com")
    if not args.backend and not api_key:
        print("[ERR] HEYGEN_API_KEY не установлен. Либо передайте --backend для проверки через собственный бэкенд.")
        return 2

    session = build_session()

    try:
        if args.backend:
            print("== Проверка через ваш бэкенд ==")
            check_via_backend(session, args.backend, args.video)
        else:
            print("== Прямая проверка доступа к HeyGen ==")
            check_avatars(session, base_url, api_key)
            status = check_status(session, base_url, api_key, args.video)
            # Пробуем прямую загрузку по API (если статус готов)
            try_download_small_chunk(session, base_url, api_key, args.video)
    except requests.HTTPError as e:
        print(f"[HTTP ERR] {e}")
        try:
            print("Body:", e.response.text[:500])
        except Exception:
            pass
        return 1
    except Exception as e:
        print(f"[ERR] {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

 

