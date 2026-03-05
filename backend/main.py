"""
Главный файл FastAPI приложения
AI Course Builder Web Platform
"""
import os
import sys
import ssl
import logging
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# ---------- SSL FIX для корпоративных сетей ----------
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''
ssl._create_default_https_context = ssl._create_unverified_context
# ----------------------------------------------------

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создаем FastAPI приложение
app = FastAPI(
    title="AI Course Builder API",
    description="API для создания и управления IT-курсами с помощью AI",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Настройка CORS для работы с React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://course-builder-frontend.onrender.com",  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Импортируем роутеры (разделенные на модули)
from backend.api.courses_routes import router as courses_router
from backend.api.modules_routes import router as modules_router
from backend.api.lessons_routes import router as lessons_router
from backend.routes.video_routes import router as video_router

# Подключаем роутеры
app.include_router(courses_router)
app.include_router(modules_router)
app.include_router(lessons_router)
app.include_router(video_router)


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "AI Course Builder API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs"
    }


@app.get("/health")
async def health_check():
    """Проверка работоспособности API (для Render)"""
    return {
        "status": "healthy",
        "service": "AI Course Builder",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")),
        "heygen_configured": bool(os.getenv("HEYGEN_API_KEY"))
    }


@app.get("/api/health")
async def health_check_api():
    """Проверка работоспособности API (альтернативный путь)"""
    return {
        "status": "healthy",
        "service": "AI Course Builder",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")),
        "heygen_configured": bool(os.getenv("HEYGEN_API_KEY"))
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Запуск AI Course Builder API...")
    logger.info("📚 Документация доступна на: http://localhost:8000/api/docs")
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

