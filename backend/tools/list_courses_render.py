"""
Скрипт для проверки списка курсов в базе данных Render (продакшн).

Использование:
    python backend/tools/list_courses_render.py
    
    Или с указанием DATABASE_URL:
    DATABASE_URL=postgresql://... python backend/tools/list_courses_render.py
"""
import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.db_postgres import RenderDatabase


def list_courses_render(database_url: str = None):
    """Выводит список всех курсов в базе данных Render"""
    
    if not database_url:
        database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("\n❌ Ошибка: DATABASE_URL не найден!")
        print("\nКак получить DATABASE_URL:")
        print("1. Зайдите в Render Dashboard: https://dashboard.render.com")
        print("2. Выберите ваш PostgreSQL сервис")
        print("3. Скопируйте 'Internal Database URL' или 'External Database URL'")
        print("4. Установите переменную окружения:")
        print("   Windows PowerShell:")
        print("   $env:DATABASE_URL='postgresql://user:pass@host:port/dbname'")
        print("   ")
        print("   Или запустите скрипт с переменной:")
        print("   $env:DATABASE_URL='...'; python backend/tools/list_courses_render.py")
        print("\n⚠️  ВАЖНО: Не коммитьте DATABASE_URL в Git!")
        return
    
    try:
        print(f"\n{'='*80}")
        print(f"Подключение к базе данных Render...")
        print(f"{'='*80}\n")
        
        # Создаем подключение к Render базе данных
        db = RenderDatabase(database_url)
        
        print("✅ Подключение успешно!\n")
        
        # Получаем список всех курсов
        courses_list = db.get_all_courses(limit=100, offset=0)
        
        if not courses_list:
            print("❌ Курсы не найдены в базе данных")
            return
        
        print(f"{'='*80}")
        print(f"Список всех курсов в базе данных Render:")
        print(f"{'='*80}\n")
        
        print(f"{'ID':<6} {'Название курса':<50} {'Создан':<20}")
        print("-" * 80)
        
        for course in courses_list:
            course_id = course.get('id')
            course_title = course.get('course_title', 'Без названия')
            created_at = course.get('created_at', '')
            
            # Обрезаем длинные названия
            if len(course_title) > 47:
                course_title = course_title[:44] + "..."
            
            print(f"{course_id:<6} {course_title:<50} {str(created_at)[:19] if created_at else '':<20}")
        
        print(f"\n{'='*80}")
        print(f"Всего курсов: {len(courses_list)}")
        print(f"{'='*80}\n")
        
        # Предлагаем проверить видео для конкретного курса
        if len(sys.argv) > 1:
            try:
                course_id = int(sys.argv[1])
                print(f"\nПроверка видео для курса ID={course_id}...\n")
                check_course_videos(db, course_id)
            except ValueError:
                print(f"\n⚠️  '{sys.argv[1]}' не является числом. Используйте: python backend/tools/list_courses_render.py <course_id>")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Подсказка: Убедитесь, что:")
        print("   - DATABASE_URL правильный")
        print("   - База данных доступна")
        print("   - У вас есть права доступа")


def check_course_videos(db: RenderDatabase, course_id: int):
    """Проверяет наличие видео для всех уроков курса"""
    try:
        course_data = db.get_course(course_id)
        if not course_data:
            print(f"❌ Курс с ID {course_id} не найден")
            return
        
        from backend.models.domain import Course
        course = Course(**{k: v for k, v in course_data.items() if k not in ['id', 'created_at', 'updated_at']})
        
        print(f"📚 Курс ID: {course_id} - {course.course_title}")
        print("-" * 80)
        
        total_lessons = 0
        lessons_with_video = 0
        lessons_ready = 0
        
        for module in course.modules:
            print(f"\n  📦 Модуль {module.module_number}: {module.module_title}")
            
            for lesson_idx, lesson in enumerate(module.lessons):
                total_lessons += 1
                
                # Проверяем наличие видео
                video_info = db.get_lesson_video_info(course_id, module.module_number, lesson_idx)
                
                if video_info:
                    lessons_with_video += 1
                    video_url = video_info.get('video_download_url')
                    video_status = video_info.get('video_status')
                    
                    if video_url and video_url.strip() and (not video_status or video_status in ['completed', 'ready', 'done', 'success']):
                        status_icon = "✅"
                        lessons_ready += 1
                    else:
                        status_icon = "⚠️"
                    
                    print(f"    {status_icon} Урок {lesson_idx + 1}: {lesson.lesson_title}")
                    print(f"        video_id: {video_info.get('video_id', 'нет')}")
                    print(f"        video_status: {video_info.get('video_status', 'нет')}")
                    print(f"        video_url: {'есть' if video_url and video_url.strip() else 'нет'}")
                else:
                    print(f"    ❌ Урок {lesson_idx + 1}: {lesson.lesson_title} (видео нет)")
        
        print(f"\n  Итого для курса {course_id}:")
        print(f"    Всего уроков: {total_lessons}")
        print(f"    Уроков с видео: {lessons_with_video}")
        print(f"    Уроков готовых для экспорта: {lessons_ready}")
        print(f"\n{'='*80}\n")
        
    except Exception as e:
        print(f"❌ Ошибка при проверке видео: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Проверяем аргументы командной строки
    database_url = None
    if len(sys.argv) > 1 and sys.argv[1].startswith('postgresql://'):
        database_url = sys.argv[1]
        sys.argv = [sys.argv[0]] + sys.argv[2:]  # Убираем DATABASE_URL из аргументов
    
    list_courses_render(database_url)

