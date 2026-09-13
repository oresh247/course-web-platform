"""Изолированный локальный сервер для проверки Course Brief MVP.

Запускается командой ``python -m uvicorn backend.local_demo:app``. В нём нет
устаревших AI-маршрутов, поэтому для проверки интервью не нужен ключ модели.
"""
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
LOCAL_DATA_DIR = ROOT_DIR / ".local"
LOCAL_DATA_DIR.mkdir(exist_ok=True)

# Эти значения задаются до импорта базы и маршрута.
os.environ["COURSE_BRIEF_DEMO_MODE"] = "true"
DEMO_DATABASE_PATH = LOCAL_DATA_DIR / "course-brief-demo.db"
# Demo-entrypoint всегда изолирован от рабочей SQLite/PostgreSQL базы, даже
# если переменные окружения были заданы в пользовательской сессии.
os.environ["DATABASE_PATH"] = str(DEMO_DATABASE_PATH)
os.environ.pop("DATABASE_URL", None)

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from backend.api.course_briefs_routes import (  # noqa: E402
    router as course_briefs_router,
)


app = FastAPI(
    title="AI Course Builder — Course Brief local demo",
    description=(
        "Локальная проверка интервью по структуре курса " "без внешней модели."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    # Vite может выбрать другой свободный порт при локальной проверке. В demo
    # режиме разрешаем только loopback-адреса, но не произвольные origins.
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(course_briefs_router)


@app.get("/api/health")
async def health_check() -> dict:
    """Возвращает признак безопасного локального demo-режима."""
    return {
        "status": "healthy",
        "service": "course-brief-demo",
        "demo_mode": True,
    }
