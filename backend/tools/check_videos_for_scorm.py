"""
Скрипт для проверки видео в базе данных перед SCORM экспортом.

Использование:
    python backend/tools/check_videos_for_scorm.py <course_id> [--url API_URL]
    
Пример:
    python backend/tools/check_videos_for_scorm.py 12 --url https://course-builder-api.onrender.com
"""
import sys
import os
import requests
import urllib3

# Отключаем предупреждения SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database.db_postgres import RenderDatabase


def check_videos_for_scorm(course_id: int, database_url: str = None):
    """Проверяет наличие видео для всех уроков курса"""
    
    if not database_url:
        database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("\n❌ Ошибка: DATABASE_URL не найден!")
        print("\nКак получить DATABASE_URL:")
        print("1. Зайдите в Render Dashboard: https://dashboard.render.com")
        print("2. Выберите ваш PostgreSQL сервис")
        print("3. Скопируйте 'External Database URL'")
        print("4. Установите переменную окружения:")
        print("   Windows PowerShell: $env:DATABASE_URL='postgresql://...'")
        return
    
    try:
        print(f"\n{'='*80}")
        print(f"Проверка видео для SCORM экспорта курса ID: {course_id}")
        print(f"{'='*80}\n")
        
        # Создаем подключение к Render базе данных
        db = RenderDatabase(database_url)
        
        # Получаем курс
        course_data = db.get_course(course_id)
        if not course_data:
            print(f"❌ Курс с ID {course_id} не найден")
            return
        
        from backend.models.domain import Course
        course = Course(**{k: v for k, v in course_data.items() if k not in ['id', 'created_at', 'updated_at']})
        
        print(f"📚 Курс: {course.course_title}\n")
        
        total_lessons = 0
        lessons_with_video = 0
        lessons_ready_for_export = 0
        lessons_missing_video = []
        
        valid_statuses = ['completed', 'ready', 'done', 'success', 'finished', 'available']
        
        for module in course.modules:
            print(f"📦 Модуль {module.module_number}: {module.module_title}")
            print("-" * 80)
            
            for lesson_idx, lesson in enumerate(module.lessons):
                total_lessons += 1
                
                # Получаем информацию о видео
                video_info = db.get_lesson_video_info(course_id, module.module_number, lesson_idx)
                
                print(f"\n  Урок {lesson_idx + 1}: {lesson.lesson_title}")
                
                if video_info:
                    lessons_with_video += 1
                    video_id = video_info.get('video_id')
                    video_url = video_info.get('video_download_url')
                    video_status = video_info.get('video_status')
                    
                    print(f"    video_id: {video_id}")
                    print(f"    video_status: {video_status}")
                    print(f"    video_url: {'есть' if video_url and video_url.strip() else 'нет'}")
                    
                    # Проверяем, готово ли видео для экспорта
                    if video_url and video_url.strip():
                        if video_status is None or video_status.lower() in [s.lower() for s in valid_statuses]:
                            lessons_ready_for_export += 1
                            print(f"    ✅ Готово для экспорта")
                        else:
                            print(f"    ⚠️ Статус '{video_status}' не подходит для экспорта")
                            lessons_missing_video.append({
                                'module': module.module_number,
                                'lesson': lesson_idx,
                                'title': lesson.lesson_title,
                                'reason': f"Статус '{video_status}' не подходит"
                            })
                    else:
                        print(f"    ❌ Нет video_download_url")
                        lessons_missing_video.append({
                            'module': module.module_number,
                            'lesson': lesson_idx,
                            'title': lesson.lesson_title,
                            'reason': 'Нет video_download_url'
                        })
                else:
                    print(f"    ❌ Видео не найдено в базе данных")
                    lessons_missing_video.append({
                        'module': module.module_number,
                        'lesson': lesson_idx,
                        'title': lesson.lesson_title,
                        'reason': 'Видео не найдено в БД'
                    })
        
        print(f"\n{'='*80}")
        print(f"Итого:")
        print(f"  Всего уроков: {total_lessons}")
        print(f"  Уроков с видео в БД: {lessons_with_video}")
        print(f"  Уроков готовых для экспорта: {lessons_ready_for_export}")
        print(f"  Уроков без видео: {total_lessons - lessons_ready_for_export}")
        print(f"{'='*80}\n")
        
        if lessons_missing_video:
            print(f"⚠️ Уроки без видео или с проблемами:")
            for item in lessons_missing_video:
                print(f"  - Модуль {item['module']}, Урок {item['lesson'] + 1}: {item['title']}")
                print(f"    Причина: {item['reason']}")
            print()
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python backend/tools/check_videos_for_scorm.py <course_id> [--url DATABASE_URL]")
        print("Пример: python backend/tools/check_videos_for_scorm.py 12 --url postgresql://...")
        sys.exit(1)
    
    course_id = int(sys.argv[1])
    database_url = None
    
    if '--url' in sys.argv:
        url_index = sys.argv.index('--url')
        if url_index + 1 < len(sys.argv):
            database_url = sys.argv[url_index + 1]
    
    check_videos_for_scorm(course_id, database_url)

