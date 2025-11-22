"""
Скрипт для поиска курса по названию и проверки видео.

Использование:
    python backend/tools/find_course_by_name.py "ETL"
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import db


def find_course(search_term):
    """Ищет курс по названию"""
    print(f"\n{'='*80}")
    print(f"Поиск курсов содержащих: '{search_term}'")
    print(f"{'='*80}\n")
    
    courses_list = db.get_all_courses(limit=100, offset=0)
    
    found = False
    for course_summary in courses_list:
        course_title = course_summary.get('course_title', '')
        if search_term.lower() in course_title.lower():
            found = True
            course_id = course_summary.get('id')
            print(f"✅ Найден курс: ID={course_id}, Название='{course_title}'")
            print(f"\nПроверка видео для этого курса...\n")
            
            # Запускаем проверку всех уроков
            from backend.tools.check_lesson_video_info import list_all_lessons_with_videos
            list_all_lessons_with_videos(course_id)
    
    if not found:
        print(f"❌ Курсы содержащие '{search_term}' не найдены")
        print(f"\nДоступные курсы:")
        for course_summary in courses_list:
            print(f"  ID={course_summary.get('id')}: {course_summary.get('course_title')}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python backend/tools/find_course_by_name.py <поисковый_термин>")
        print("Пример: python backend/tools/find_course_by_name.py ETL")
        sys.exit(1)
    
    search_term = sys.argv[1]
    find_course(search_term)

