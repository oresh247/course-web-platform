"""
Скрипт для проверки ответа API /api/courses/{id} и наличия content_outline в уроках.

Использование:
    python backend/tools/check_course_api_response.py <course_id>
    
Пример:
    python backend/tools/check_course_api_response.py 12
"""
import sys
import os
import json
import requests
import ssl
import urllib3

# Отключаем предупреждения SSL для корпоративных сетей
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


def check_course_api(course_id: int, api_url: str = None):
    """Проверяет ответ API для курса"""
    
    if not api_url:
        # Пробуем определить URL из переменных окружения или используем локальный
        api_url = os.getenv('API_URL', 'http://localhost:8000')
    
    url = f"{api_url}/api/courses/{course_id}"
    
    print(f"\n{'='*80}")
    print(f"Проверка API ответа для курса ID: {course_id}")
    print(f"URL: {url}")
    print(f"{'='*80}\n")
    
    try:
        # Отключаем проверку SSL для корпоративных сетей
        response = requests.get(url, timeout=10, verify=False)
        response.raise_for_status()
        
        data = response.json()
        
        # Проверяем структуру ответа
        if 'course' in data:
            course = data['course']
        elif 'course_title' in data:
            course = data
        else:
            print("❌ Неожиданная структура ответа API")
            print(f"Ключи в ответе: {list(data.keys())}")
            return
        
        print(f"✅ Курс найден: {course.get('course_title', 'Без названия')}\n")
        
        # Проверяем модули и уроки
        modules = course.get('modules', [])
        print(f"📦 Модулей: {len(modules)}\n")
        
        total_lessons = 0
        lessons_with_outline = 0
        lessons_without_outline = 0
        
        for module in modules:
            module_number = module.get('module_number', '?')
            module_title = module.get('module_title', 'Без названия')
            lessons = module.get('lessons', [])
            
            print(f"  📦 Модуль {module_number}: {module_title}")
            print(f"     Уроков: {len(lessons)}")
            
            for idx, lesson in enumerate(lessons):
                total_lessons += 1
                lesson_title = lesson.get('lesson_title', 'Без названия')
                content_outline = lesson.get('content_outline')
                
                print(f"\n     Урок {idx + 1}: {lesson_title}")
                print(f"       Ключи в объекте урока: {list(lesson.keys())}")
                
                if content_outline is not None:
                    lessons_with_outline += 1
                    if isinstance(content_outline, list):
                        print(f"       ✅ content_outline есть (массив, {len(content_outline)} пунктов):")
                        for i, item in enumerate(content_outline[:3], 1):  # Показываем первые 3
                            print(f"          {i}. {item}")
                        if len(content_outline) > 3:
                            print(f"          ... и еще {len(content_outline) - 3} пунктов")
                    elif isinstance(content_outline, str):
                        print(f"       ✅ content_outline есть (строка):")
                        print(f"          {content_outline[:100]}...")
                    else:
                        print(f"       ⚠️ content_outline есть, но неожиданный тип: {type(content_outline)}")
                        print(f"          Значение: {content_outline}")
                else:
                    lessons_without_outline += 1
                    print(f"       ❌ content_outline отсутствует")
                    print(f"       Доступные поля: {list(lesson.keys())}")
            
            print()
        
        print(f"\n{'='*80}")
        print(f"Итого:")
        print(f"  Всего уроков: {total_lessons}")
        print(f"  Уроков с content_outline: {lessons_with_outline}")
        print(f"  Уроков без content_outline: {lessons_without_outline}")
        print(f"{'='*80}\n")
        
        # Сохраняем полный ответ в файл для детального анализа
        output_file = f"course_{course_id}_api_response.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Полный ответ API сохранен в файл: {output_file}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при запросе к API: {e}")
        print(f"\n💡 Попробуйте:")
        print(f"   1. Проверить, что API запущен на {api_url}")
        print(f"   2. Использовать другой URL: python backend/tools/check_course_api_response.py {course_id} --url https://course-builder-api.onrender.com")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python backend/tools/check_course_api_response.py <course_id> [--url API_URL]")
        print("Пример: python backend/tools/check_course_api_response.py 12")
        print("Пример: python backend/tools/check_course_api_response.py 12 --url https://course-builder-api.onrender.com")
        sys.exit(1)
    
    course_id = int(sys.argv[1])
    api_url = None
    
    # Проверяем аргумент --url
    if '--url' in sys.argv:
        url_index = sys.argv.index('--url')
        if url_index + 1 < len(sys.argv):
            api_url = sys.argv[url_index + 1]
    
    check_course_api(course_id, api_url)

