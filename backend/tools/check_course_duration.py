"""
Проверка наличия длительности курса (duration_weeks / duration_hours) в БД.

Запуск (из корня проекта):
  py backend/tools/check_course_duration.py --id 7

Скрипт сам подхватит backend/.env и определит хранилище (Postgres Render или локальный SQLite).
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv


def main() -> int:
    # Загружаем окружение из backend/.env и корневого .env
    # Добавляем корень проекта в PYTHONPATH, чтобы работали импорты 'backend.*'
    this_file = Path(__file__).resolve()
    backend_dir = this_file.parent.parent  # backend/
    project_root = backend_dir.parent      # корень проекта
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Загружаем .env
    load_dotenv(str(backend_dir / ".env"))
    load_dotenv(str(project_root / ".env"))

    parser = argparse.ArgumentParser()
    parser.add_argument("--id", type=int, required=True, help="ID курса")
    args = parser.parse_args()

    # Получаем БД через фабрику (поддержка Postgres/SQLite)
    try:
        from backend.database.db_postgres import get_database  # type: ignore
        db = get_database()
    except Exception:
        # Фоллбек на локальную БД
        from backend.database.db import db  # type: ignore

    course = db.get_course(args.id)
    if not course:
        print(f"[NOT FOUND] Курс {args.id} не найден")
        return 1

    dw = course.get("duration_weeks")
    dh = course.get("duration_hours")
    title = course.get("course_title")
    print(f"ID={args.id} | title='{title}' | duration_weeks={dw} | duration_hours={dh}")
    if dw or dh:
        print("[OK] Длительность присутствует")
        return 0
    else:
        print("[MISS] Длительность отсутствует в данных курса")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())


