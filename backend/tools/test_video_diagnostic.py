"""
Тестовый скрипт для диагностики проблем с просмотром и скачиванием видео
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_video_info_api(course_id, module_number, lesson_index):
    """Тестирует получение информации о видео из API"""
    print(f"\n{'='*60}")
    print(f"Тест получения информации о видео")
    print(f"{'='*60}")
    print(f"Курс ID: {course_id}")
    print(f"Модуль: {module_number}")
    print(f"Урок: {lesson_index}")
    
    try:
        url = f"{BASE_URL}/api/video/lesson/{course_id}/{module_number}/{lesson_index}/info"
        print(f"\n📡 Запрос к: {url}")
        
        response = requests.get(url)
        print(f"✅ HTTP статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📦 Ответ API:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if data.get('success') and data.get('data'):
                video_info = data['data']
                print(f"\n✅ Информация о видео найдена:")
                print(f"   - video_id: {video_info.get('video_id')}")
                print(f"   - video_status: {video_info.get('video_status')}")
                print(f"   - video_download_url: {video_info.get('video_download_url')}")
                print(f"   - video_generated_at: {video_info.get('video_generated_at')}")
                
                if video_info.get('video_download_url'):
                    print(f"\n🔗 URL для скачивания:")
                    print(f"   {video_info['video_download_url']}")
                    return True, video_info
                else:
                    print(f"\n❌ URL для скачивания отсутствует!")
                    return False, None
            else:
                print(f"\n⚠️ Видео не найдено в БД")
                return False, None
        else:
            print(f"\n❌ Ошибка HTTP {response.status_code}")
            print(response.text)
            return False, None
            
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_video_status_api(video_id):
    """Тестирует получение статуса видео из HeyGen"""
    print(f"\n{'='*60}")
    print(f"Тест статуса видео HeyGen")
    print(f"{'='*60}")
    print(f"Video ID: {video_id}")
    
    try:
        url = f"{BASE_URL}/api/video/status/{video_id}"
        print(f"\n📡 Запрос к: {url}")
        
        response = requests.get(url)
        print(f"✅ HTTP статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n📦 Ответ API:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if data.get('success') and data.get('data'):
                status = data['data']
                print(f"\n✅ Статус видео:")
                print(f"   - status: {status.get('status')}")
                print(f"   - progress: {status.get('progress')}%")
                print(f"   - download_url: {status.get('download_url')}")
                return True, status
            else:
                print(f"\n⚠️ Статус не получен")
                return False, None
        else:
            print(f"\n❌ Ошибка HTTP {response.status_code}")
            print(response.text)
            return False, None
            
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_video_download(video_url):
    """Тестирует доступность URL для скачивания"""
    print(f"\n{'='*60}")
    print(f"Тест доступности URL видео")
    print(f"{'='*60}")
    print(f"URL: {video_url}")
    
    try:
        # Делаем HEAD запрос для проверки доступности
        print(f"\n📡 Проверка доступности URL (HEAD запрос)...")
        response = requests.head(video_url, allow_redirects=True, timeout=10)
        
        print(f"✅ HTTP статус: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"   Content-Length: {response.headers.get('Content-Length', 'N/A')}")
        
        if response.status_code == 200:
            print(f"\n✅ URL доступен для скачивания!")
            return True
        elif response.status_code in [301, 302, 303, 307, 308]:
            redirect_url = response.headers.get('Location', 'N/A')
            print(f"\n⚠️ Перенаправление на: {redirect_url}")
            return True
        else:
            print(f"\n❌ URL недоступен (статус {response.status_code})")
            return False
            
    except Exception as e:
        print(f"\n❌ Ошибка проверки URL: {e}")
        import traceback
        traceback.print_exc()
        return False


def list_all_lessons_with_videos():
    """Получает список всех уроков с видео"""
    print(f"\n{'='*60}")
    print(f"Поиск всех уроков с видео в базе данных")
    print(f"{'='*60}")
    
    try:
        # Получаем список всех курсов
        url = f"{BASE_URL}/api/courses/?limit=100&offset=0"
        print(f"\n📡 Запрос списка курсов: {url}")
        
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Ошибка получения курсов: {response.status_code}")
            return []
        
        courses_data = response.json()
        # API может возвращать список напрямую или объект с полем courses
        if isinstance(courses_data, list):
            courses = courses_data
        elif isinstance(courses_data, dict):
            courses = courses_data.get('courses', courses_data.get('data', []))
        else:
            courses = []
        print(f"✅ Найдено курсов: {len(courses)}")
        
        lessons_with_video = []
        total_lessons_checked = 0
        
        for course in courses:
            course_id = course.get('id')
            course_title = course.get('course_title', 'N/A')
            
            if not course_id:
                print(f"\n⚠️ Пропуск курса без ID: {course_title}")
                continue
            
            print(f"\n📚 Проверка курса: {course_title} (ID: {course_id})")
            
            # Получаем детали курса
            course_detail_url = f"{BASE_URL}/api/courses/{course_id}"
            try:
                course_response = requests.get(course_detail_url, timeout=5)
                
                if course_response.status_code != 200:
                    print(f"   ❌ Не удалось загрузить детали курса: HTTP {course_response.status_code}")
                    continue
            except Exception as e:
                print(f"   ❌ Ошибка загрузки деталей курса: {e}")
                continue
            
            try:
                course_data = course_response.json()
                # API может возвращать объект с полем 'course' или напрямую объект курса
                if isinstance(course_data, dict) and 'course' in course_data:
                    course_data = course_data['course']
            except:
                course_data = course_response.json()
            
            if not course_data or not course_data.get('modules'):
                print(f"   ⚠️ Курс не содержит модулей")
                continue
            
            modules = course_data.get('modules', [])
            print(f"   📦 Найдено модулей: {len(modules)}")
            
            # Проверяем каждый модуль и урок
            for module in modules:
                module_number = module.get('module_number', 0)
                module_title = module.get('module_title', 'N/A')
                lessons = module.get('lessons', [])
                
                if not lessons:
                    continue
                
                print(f"   📄 Модуль {module_number}: {module_title} ({len(lessons)} уроков)")
                
                for lesson_index, lesson in enumerate(lessons):
                    total_lessons_checked += 1
                    lesson_title = lesson.get('lesson_title', 'N/A')
                    
                    # Проверяем наличие видео
                    video_info_url = f"{BASE_URL}/api/video/lesson/{course_id}/{module_number}/{lesson_index}/info"
                    try:
                        video_response = requests.get(video_info_url, timeout=5)
                        
                        if video_response.status_code == 200:
                            video_data = video_response.json()
                            
                            if video_data.get('success') and video_data.get('data'):
                                video_info = video_data['data']
                                
                                if video_info:
                                    video_status = video_info.get('video_status', 'N/A')
                                    video_url = video_info.get('video_download_url')
                                    
                                    print(f"      ✅ Урок {lesson_index}: {lesson_title}")
                                    print(f"         Статус: {video_status}")
                                    print(f"         URL: {'✅ Есть' if video_url else '❌ Нет'}")
                                    
                                    if video_url:
                                        lessons_with_video.append({
                                            'course_id': course_id,
                                            'course_title': course_title,
                                            'module_number': module_number,
                                            'module_title': module_title,
                                            'lesson_index': lesson_index,
                                            'lesson_title': lesson_title,
                                            'video_info': video_info
                                        })
                        elif video_response.status_code == 404:
                            # Это нормально - видео может быть не сгенерировано
                            pass
                        else:
                            print(f"      ⚠️ Урок {lesson_index}: {lesson_title} - ошибка HTTP {video_response.status_code}")
                    except Exception as e:
                        print(f"      ❌ Ошибка проверки урока {lesson_index}: {e}")
        
        return lessons_with_video
        
    except Exception as e:
        print(f"\n❌ Ошибка поиска уроков с видео: {e}")
        import traceback
        traceback.print_exc()
        return []


def main():
    print("="*60)
    print("ТЕСТ ДИАГНОСТИКИ ВИДЕО")
    print("="*60)
    
    # Вариант 1: Использовать аргументы командной строки
    if len(sys.argv) >= 4:
        course_id = int(sys.argv[1])
        module_number = int(sys.argv[2])
        lesson_index = int(sys.argv[3])
        
        success, video_info = test_video_info_api(course_id, module_number, lesson_index)
        
        if success and video_info:
            video_id = video_info.get('video_id')
            download_url = video_info.get('video_download_url')
            
            if video_id:
                test_video_status_api(video_id)
            
            if download_url:
                test_video_download(download_url)
    
    # Вариант 2: Автоматический поиск всех уроков с видео
    else:
        print("\n🔍 Поиск всех уроков с видео в системе...")
        lessons_with_video = list_all_lessons_with_videos()
        
        print(f"\n{'='*60}")
        print(f"РЕЗУЛЬТАТЫ ПОИСКА")
        print(f"{'='*60}")
        print(f"Уроков с видео найдено: {len(lessons_with_video)}")
        
        if lessons_with_video:
            print(f"\n{'='*60}")
            print("📹 СПИСОК УРОКОВ С ВИДЕО:")
            print(f"{'='*60}")
            
            for i, lesson in enumerate(lessons_with_video, 1):
                print(f"\n{i}. Курс: {lesson['course_title']}")
                print(f"   Модуль {lesson['module_number']}: {lesson['module_title']}")
                print(f"   Урок {lesson['lesson_index']}: {lesson['lesson_title']}")
                video_info = lesson['video_info']
                print(f"   Video ID: {video_info.get('video_id', 'N/A')}")
                print(f"   Status: {video_info.get('video_status', 'N/A')}")
                print(f"   URL: {video_info.get('video_download_url', 'N/A')[:80]}..." if video_info.get('video_download_url') else "   URL: ❌ Нет")
                print(f"   Generated: {video_info.get('video_generated_at', 'N/A')}")
            
            # Тестируем первый найденный урок
            if lessons_with_video:
                first_lesson = lessons_with_video[0]
                print(f"\n{'='*60}")
                print("Тестирование первого найденного урока:")
                print(f"{'='*60}")
                
                test_video_info_api(
                    first_lesson['course_id'],
                    first_lesson['module_number'],
                    first_lesson['lesson_index']
                )
                
                video_info = first_lesson['video_info']
                if video_info.get('video_id'):
                    test_video_status_api(video_info['video_id'])
                
                if video_info.get('video_download_url'):
                    test_video_download(video_info['video_download_url'])
        else:
            print("\n❌ Уроки с готовым видео не найдены")
            print("\n💡 Возможные причины:")
            print("   1. Видео еще не были сгенерированы")
            print("   2. Видео сгенерированы, но статус не 'completed'")
            print("   3. Видео готовы, но download_url не сохранен в БД")
            print("   4. Проблема с сохранением данных в базу данных")
            print("\n💡 Проверьте:")
            print("   - Файл video_cache.json в backend/")
            print("   - Логи backend сервера при генерации видео")
            print("   - Базу данных (lesson_contents таблица)")
            print("\n💡 Использование для тестирования конкретного урока:")
            print("   python test_video_diagnostic.py <course_id> <module_number> <lesson_index>")
            print("\n   Пример:")
            print("   python test_video_diagnostic.py 3 1 0")
    
    print(f"\n{'='*60}")
    print("Тестирование завершено")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()


