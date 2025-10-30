import sqlite3
import json
import re

DB_PATH = "courses.db"  # Измени путь при необходимости

COURSE_ID = 3
MODULE_NUMBER = 1
LESSON_INDEX = 0

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("== Структура таблицы lesson_contents ==")
    cursor.execute("PRAGMA table_info(lesson_contents);")
    cols = cursor.fetchall()
    for col in cols:
        print(col)

    print("\n== Значения полей с video в названии ==")
    cursor.execute(
        "SELECT * FROM lesson_contents WHERE course_id=? AND module_number=? AND lesson_index=?;",
        (COURSE_ID, MODULE_NUMBER, LESSON_INDEX),
    )
    row = cursor.fetchone()
    if not row:
        print("Нет записи для course_id=3, module_number=1, lesson_index=0.")
        return

    colnames = [desc[0] for desc in cursor.description]

    found_any = False
    for name, val in zip(colnames, row):
        if 'video' in name.lower():
            found_any = True
            print(f"Поле {name}: {val}")
            if isinstance(val, str) and ('{' in val or '[' in val):
                try:
                    parsed = json.loads(val)
                    print(f"  JSON объект: {parsed}")
                except Exception:
                    pass

    if not found_any:
        print("В явных полях с video в названии ничего не найдено.")

    print("\n== Поиск video_id по всем строковым/JSON полям ==")
    for name, val in zip(colnames, row):
        if isinstance(val, str):
            if re.search(r'video.?id', val, re.I) or re.search(r'heygen', val, re.I):
                print(f"Поле {name} содержит в себе video_id или подобную инфу:")
                print(val[:500])

if __name__ == "__main__":
    main()
