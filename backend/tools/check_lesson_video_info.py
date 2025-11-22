"""
Скрипт для проверки информации о видео для урока в базе данных.

Использование:
    python backend/tools/check_lesson_video_info.py <course_id> <module_number> <lesson_index>
    
Пример:
    python backend/tools/check_lesson_video_info.py 1 1 0
"""
import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.database import db
import json


def check_lesson_video_info(course_id: int, module_number: int, lesson_index: int):
    """Проверяет информацию о видео для урока"""
    
    print(f"\n{'='*60}")
    print(f"Проверка видео для урока:")
    print(f"  Курс ID: {course_id}")
    print(f"  Модуль: {module_number}")
    print(f"  Урок (индекс): {lesson_index}")
    print(f"{'='*60}\n")
    
    # Получаем детальный контент урока
    content_data = db.get_lesson_content(course_id, module_number, lesson_index)
    
    if not content_data:
        print("❌ Детальный контент урока не найден в базе данных")
        print("\nПопытка получить информацию о видео напрямую...")
        
        # Пытаемся получить информацию о видео напрямую
        video_info = db.get_lesson_video_info(course_id, module_number, lesson_index)
        if video_info:
            print("✅ Информация о видео найдена напрямую:")
            print_video_info(video_info)
        else:
            print("❌ Информация о видео не найдена")
        return
    
    print("✅ Детальный контент урока найден")
    
    # Проверяем информацию о видео
    video_info = content_data.get('video_info')
    
    if not video_info:
        print("❌ Информация о видео отсутствует в content_data")
        print("\nПопытка получить информацию о видео напрямую...")
        
        video_info = db.get_lesson_video_info(course_id, module_number, lesson_index)
        if video_info:
            print("✅ Информация о видео найдена напрямую:")
            print_video_info(video_info)
        else:
            print("❌ Информация о видео не найдена в базе данных")
        return
    
    print("\n📹 Информация о видео:")
    print_video_info(video_info)
    
    # Проверяем готовность видео для SCORM экспорта
    print("\n🔍 Проверка готовности для SCORM экспорта:")
    
    video_id = video_info.get('video_id')
    video_url = video_info.get('video_download_url')
    video_status = video_info.get('video_status')
    
    checks = []
    
    if video_id:
        checks.append(("✅", f"video_id: {video_id}"))
    else:
        checks.append(("⚠️", "video_id отсутствует"))
    
    if video_url and video_url.strip():
        checks.append(("✅", f"video_download_url: {video_url[:80]}..."))
    else:
        checks.append(("❌", "video_download_url отсутствует или пустой"))
    
    if video_status:
        if video_status in ['completed', 'ready', 'done', 'success']:
            checks.append(("✅", f"video_status: {video_status} (подходит для экспорта)"))
        else:
            checks.append(("⚠️", f"video_status: {video_status} (не подходит для экспорта)"))
    else:
        checks.append(("⚠️", "video_status не указан"))
    
    for status, message in checks:
        print(f"  {status} {message}")
    
    # Итоговый вердикт
    print("\n" + "="*60)
    if video_url and video_url.strip() and (not video_status or video_status in ['completed', 'ready', 'done', 'success']):
        print("✅ ВИДЕО ГОТОВО ДЛЯ SCORM ЭКСПОРТА")
    else:
        print("❌ ВИДЕО НЕ ГОТОВО ДЛЯ SCORM ЭКСПОРТА")
        if not video_url or not video_url.strip():
            print("   Причина: отсутствует video_download_url")
        elif video_status and video_status not in ['completed', 'ready', 'done', 'success']:
            print(f"   Причина: неподходящий статус '{video_status}'")
    print("="*60 + "\n")


def print_video_info(video_info: dict):
    """Выводит информацию о видео в читаемом формате"""
    print(f"  video_id: {video_info.get('video_id', 'не указан')}")
    print(f"  video_download_url: {video_info.get('video_download_url', 'не указан')}")
    print(f"  video_status: {video_info.get('video_status', 'не указан')}")
    print(f"  video_generated_at: {video_info.get('video_generated_at', 'не указан')}")


def list_all_lessons_with_videos(course_id: int):
    """Выводит список всех уроков курса с информацией о видео"""
    print(f"\n{'='*60}")
    print(f"Список всех уроков курса {course_id} с информацией о видео:")
    print(f"{'='*60}\n")
    
    # Получаем курс
    course_data = db.get_course(course_id)
    if not course_data:
        print(f"❌ Курс с ID {course_id} не найден")
        return
    
    from backend.models.domain import Course
    course = Course(**{k: v for k, v in course_data.items() if k not in ['id', 'created_at', 'updated_at']})
    
    total_lessons = 0
    lessons_with_video = 0
    lessons_ready_for_export = 0
    
    for module in course.modules:
        print(f"\n📦 Модуль {module.module_number}: {module.module_title}")
        print("-" * 60)
        
        for lesson_idx, lesson in enumerate(module.lessons):
            total_lessons += 1
            content_data = db.get_lesson_content(course_id, module.module_number, lesson_idx)
            video_info = None
            
            if content_data:
                video_info = content_data.get('video_info')
            
            if not video_info:
                video_info = db.get_lesson_video_info(course_id, module.module_number, lesson_idx)
            
            video_url = video_info.get('video_download_url') if video_info else None
            video_status = video_info.get('video_status') if video_info else None
            
            status_icon = "❌"
            if video_info:
                lessons_with_video += 1
                if video_url and video_url.strip() and (not video_status or video_status in ['completed', 'ready', 'done', 'success']):
                    status_icon = "✅"
                    lessons_ready_for_export += 1
                else:
                    status_icon = "⚠️"
            
            print(f"  {status_icon} Урок {lesson_idx + 1}: {lesson.lesson_title}")
            if video_info:
                print(f"      video_id: {video_info.get('video_id', 'нет')}")
                print(f"      video_status: {video_info.get('video_status', 'нет')}")
                print(f"      video_url: {'есть' if video_url else 'нет'}")
            else:
                print(f"      Видео не найдено")
    
    print(f"\n{'='*60}")
    print(f"Итого:")
    print(f"  Всего уроков: {total_lessons}")
    print(f"  Уроков с видео: {lessons_with_video}")
    print(f"  Уроков готовых для экспорта: {lessons_ready_for_export}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python backend/tools/check_lesson_video_info.py <course_id> [module_number] [lesson_index]")
        print("\nПримеры:")
        print("  python backend/tools/check_lesson_video_info.py 1 1 0  # Проверить конкретный урок")
        print("  python backend/tools/check_lesson_video_info.py 1      # Список всех уроков курса")
        sys.exit(1)
    
    course_id = int(sys.argv[1])
    
    if len(sys.argv) >= 4:
        # Проверка конкретного урока
        module_number = int(sys.argv[2])
        lesson_index = int(sys.argv[3])
        check_lesson_video_info(course_id, module_number, lesson_index)
    else:
        # Список всех уроков курса
        list_all_lessons_with_videos(course_id)

