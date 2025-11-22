"""
Скрипт для вывода списка всех курсов с их ID.

Использование:
    python backend/tools/list_all_course_ids.py
"""
import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import db


def list_all_course_ids():
    """Выводит список всех курсов с их ID"""
    print(f"\n{'='*80}")
    print(f"Список всех курсов в базе данных:")
    print(f"{'='*80}\n")
    
    try:
        courses_list = db.get_all_courses(limit=100, offset=0)
        
        if not courses_list:
            print("❌ Курсы не найдены в базе данных")
            return
        
        print(f"{'ID':<6} {'Название курса':<50} {'Создан':<20}")
        print("-" * 80)
        
        for course in courses_list:
            course_id = course.get('id')
            course_title = course.get('course_title', 'Без названия')
            created_at = course.get('created_at', '')
            
            # Обрезаем длинные названия
            if len(course_title) > 47:
                course_title = course_title[:44] + "..."
            
            print(f"{course_id:<6} {course_title:<50} {created_at:<20}")
        
        print(f"\n{'='*80}")
        print(f"Всего курсов: {len(courses_list)}")
        print(f"{'='*80}\n")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    list_all_course_ids()

