"""
Тестовый скрипт: проверяет, что при создании курса через API сохраняются поля длительности.

Запуск:
  py backend/tools/test_course_creation_duration.py --api http://localhost:8000

Поведение:
  1) POST /api/courses/ c фиктивными данными и duration_weeks/duration_hours
  2) GET /api/courses/{id} и проверка, что поля сохранены
  3) Вывод результата и краткая диагностика
"""

import os
import sys
import json
import argparse
from pathlib import Path
import requests
from dotenv import load_dotenv


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default=os.getenv("TEST_API_URL", "http://localhost:8000"), help="Базовый URL бэкенда")
    parser.add_argument("--weeks", type=int, default=8, help="duration_weeks")
    parser.add_argument("--hours", type=int, default=24, help="duration_hours")
    args = parser.parse_args()

    # Подгружаем env (на всякий случай)
    here = Path(__file__).resolve()
    backend_dir = here.parent.parent
    project_root = backend_dir.parent
    load_dotenv(str(backend_dir / ".env"))
    load_dotenv(str(project_root / ".env"))

    base_url = args.api.rstrip("/")
    session = requests.Session()
    session.verify = False  # для локальной отладки в корп. сети

    # 1) Создаём курс
    # Тело запроса согласно схеме генерации курса (topic/audience_level/module_count...)
    payload = {
        "topic": "Тест сохранения длительности",
        "audience_level": "junior",
        "module_count": 3,
        "duration_weeks": args.weeks,
        "hours_per_week": args.hours
    }

    try:
        r = session.post(f"{base_url}/api/courses/", json=payload, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"[HTTP ERR] POST /api/courses/: {e}")
        try:
            print("Body:", r.text[:500])
        except Exception:
            pass
        return 1

    resp = r.json()
    # API может вернуть целый объект с курсом или id отдельно — пробуем извлечь
    course_id = resp.get("id") or resp.get("course", {}).get("id") or resp.get("course_id")
    if not course_id:
        # Попробуем вытащить id из списка курсов как последний созданный
        print("[WARN] id не возвращён в ответе на создание, пытаюсь прочитать список курсов…")
        rr = session.get(f"{base_url}/api/courses/", timeout=20)
        rr.raise_for_status()
        all_courses = rr.json() or {}
        if isinstance(all_courses, dict) and all_courses.get("results"):
            course_id = all_courses["results"][0].get("id")
        elif isinstance(all_courses, list) and all_courses:
            course_id = all_courses[0].get("id")
    if not course_id:
        print("[ERR] Не удалось определить ID созданного курса")
        return 2

    # 2) Читаем курс и проверяем длительность
    gr = session.get(f"{base_url}/api/courses/{course_id}", timeout=20)
    try:
        gr.raise_for_status()
    except Exception as e:
        print(f"[HTTP ERR] GET /api/courses/{course_id}: {e}")
        print("Body:", gr.text[:500])
        return 3

    data = gr.json() or {}
    course = data.get("course") or data
    dw = course.get("duration_weeks")
    dh = course.get("duration_hours")
    print(f"ID={course_id} duration_weeks={dw} duration_hours={dh}")

    ok = (dw == args.weeks) and (dh == args.hours)
    if ok:
        print("[OK] Длительность сохранена корректно")
        return 0
    else:
        print("[FAIL] Длительность не совпадает с отправленной")
        return 4


if __name__ == "__main__":
    raise SystemExit(main())


