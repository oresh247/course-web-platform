"""
Скрипт для вывода списка всех курсов и уроков с видео.

Использование:
    python backend/tools/list_courses_with_videos.py
"""
import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import db


def list_all_courses(course_id: int = None):
    """Выводит список всех курсов с информацией о видео или конкретный курс"""
    if course_id:
        print(f"\n{'='*80}")
        print(f"Информация о видео для курса ID: {course_id}")
        print(f"{'='*80}\n")
    else:
        print(f"\n{'='*80}")
        print(f"Список всех курсов с информацией о видео:")
        print(f"{'='*80}\n")
    
    try:
        # Получаем список всех курсов или конкретный курс
        if course_id:
            course_data = db.get_course(course_id)
            if not course_data:
                print(f"❌ Курс с ID {course_id} не найден в базе данных")
                return
            
            # Создаем список с одним курсом для единообразной обработки
            courses_list = [{'id': course_id, 'course_title': course_data.get('course_title', 'Без названия')}]
        else:
            courses_list = db.get_all_courses(limit=100, offset=0)
        
        if not courses_list:
            print("❌ Курсы не найдены в базе данных")
            return
        
        # Для каждого курса получаем полную информацию
        for course_summary in courses_list:
            course_id = course_summary.get('id')
            course_title = course_summary.get('course_title', 'Без названия')
            
            print(f"\n📚 Курс ID: {course_id} - {course_title}")
            print("-" * 80)
            
            # Получаем полную информацию о курсе
            course_data = db.get_course(course_id)
            if not course_data:
                print("  ⚠️ Не удалось загрузить полную информацию о курсе")
                continue
            
            from backend.models.domain import Course
            try:
                course = Course(**{k: v for k, v in course_data.items() if k not in ['id', 'created_at', 'updated_at']})
            except Exception as e:
                print(f"  ⚠️ Ошибка парсинга курса: {e}")
                continue
            
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
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys
    course_id = None
    if len(sys.argv) > 1:
        try:
            course_id = int(sys.argv[1])
        except ValueError:
            print(f"❌ Ошибка: '{sys.argv[1]}' не является числом")
            print("Использование: python backend/tools/list_courses_with_videos.py [course_id]")
            print("Пример: python backend/tools/list_courses_with_videos.py 12")
            sys.exit(1)
    
    list_all_courses(course_id)

