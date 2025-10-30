import sqlite3
import json

# Путь к вашей базе данных (можно скорректировать при необходимости)
DB_PATH = "courses.db"

COURSE_ID = 3
MODULE_NUMBER = 1
LESSON_INDEX = 0

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT video_info
        FROM lesson_contents
        WHERE course_id=? AND module_number=? AND lesson_index=?
        """, (COURSE_ID, MODULE_NUMBER, LESSON_INDEX))
    row = cursor.fetchone()
    if not row:
        print("Урок не найден в базе.")
        return
    video_info_raw = row[0]
    if not video_info_raw:
        print("В поле video_info ничего нет.")
        return
    try:
        video_info = json.loads(video_info_raw)
        video_id = video_info.get("video_id")
        print(f"video_info: {video_info}")
        if video_id:
            print(f"Обнаружен video_id: {video_id}")
        else:
            print("video_id отсутствует в поле video_info.")
    except Exception as e:
        print(f"Ошибка парсинга video_info — это не JSON?: {e}")

if __name__ == "__main__":
    main()
