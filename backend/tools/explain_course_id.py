"""
Скрипт для объяснения, как узнать ID курса.

Использование:
    python backend/tools/explain_course_id.py
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import db


def explain_course_id():
    """Объясняет, как узнать ID курса"""
    print(f"\n{'='*80}")
    print(f"Как узнать ID курса:")
    print(f"{'='*80}\n")
    
    print("1. 📍 В URL браузера:")
    print("   Если вы видите URL: https://course-builder-frontend.onrender.com/courses/12")
    print("   То ID курса = 12 (последнее число в URL)\n")
    
    print("2. 📋 Список всех курсов в локальной базе данных:")
    print("   Запустите: python backend/tools/list_all_course_ids.py\n")
    
    print("3. 🔍 Проверка конкретного курса:")
    print("   Запустите: python backend/tools/list_courses_with_videos.py <course_id>\n")
    
    print("4. 🌐 Для курсов на Render (продакшн):")
    print("   ID можно увидеть только в URL или через веб-интерфейс")
    print("   Локальная база данных не содержит курсы с Render\n")
    
    print(f"{'='*80}")
    print("Курсы в локальной базе данных:")
    print(f"{'='*80}\n")
    
    try:
        courses_list = db.get_all_courses(limit=100, offset=0)
        
        if not courses_list:
            print("❌ Курсы не найдены в локальной базе данных")
            print("   (Это нормально, если вы работаете с курсами на Render)\n")
        else:
            for course in courses_list:
                course_id = course.get('id')
                course_title = course.get('course_title', 'Без названия')
                print(f"   ID: {course_id} - {course_title}")
        
        print(f"\n{'='*80}\n")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    explain_course_id()

