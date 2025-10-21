"""
Инициализация базы данных
Автоматически выбирает PostgreSQL если DATABASE_URL установлен, иначе SQLite
"""
import os
import logging

logger = logging.getLogger(__name__)

# Проверяем наличие DATABASE_URL (PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    logger.info("🐘 Используется PostgreSQL")
    from backend.database.db_postgres import db
else:
    logger.info("📁 Используется SQLite")
    from backend.database.db import db

__all__ = ["db"]
