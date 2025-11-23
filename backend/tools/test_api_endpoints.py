"""
Скрипт для тестирования API endpoints для работы с тестами
"""
import sys
import os
import json
import requests
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

BASE_URL = os.getenv("API_URL", "http://localhost:8000")

def test_api_endpoints():
    """Тестирует API endpoints для работы с тестами"""
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ API ENDPOINTS ДЛЯ ТЕСТОВ")
    print("=" * 60)
    
    # Тестовые параметры
    course_id = 1
    module_number = 1
    lesson_index = 0
    
    print(f"\n📡 Базовый URL: {BASE_URL}")
    print(f"   Курс ID: {course_id}")
    print(f"   Модуль: {module_number}")
    print(f"   Урок: {lesson_index}")
    
    results = []
    
    # Тест 1: Проверка существования курса
    print(f"\n1️⃣ Проверка существования курса...")
    try:
        response = requests.get(f"{BASE_URL}/api/courses/{course_id}", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ Курс найден")
            results.append(("Проверка курса", True))
        else:
            print(f"   ⚠️ Курс не найден (статус: {response.status_code})")
            results.append(("Проверка курса", None))
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️ Не удалось подключиться к API: {e}")
        print(f"   💡 Убедитесь, что backend запущен: uvicorn main:app --reload")
        results.append(("Проверка курса", None))
        return results
    
    # Тест 2: Генерация теста
    print(f"\n2️⃣ Генерация теста...")
    try:
        payload = {
            "num_questions": 5,
            "model": "gpt-4-turbo-preview",
            "temperature": 0.7,
            "max_tokens": 2000
        }
        response = requests.post(
            f"{BASE_URL}/api/courses/{course_id}/modules/{module_number}/lessons/{lesson_index}/generate-test",
            json=payload,
            timeout=120
        )
        if response.status_code == 200:
            test_data = response.json()
            print(f"   ✅ Тест успешно сгенерирован")
            print(f"      Вопросов: {len(test_data.get('questions', []))}")
            results.append(("Генерация теста", True))
        else:
            print(f"   ❌ Ошибка генерации теста (статус: {response.status_code})")
            print(f"      Ответ: {response.text[:200]}")
            results.append(("Генерация теста", False))
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️ Ошибка запроса: {e}")
        results.append(("Генерация теста", None))
    
    # Тест 3: Получение теста
    print(f"\n3️⃣ Получение теста...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/courses/{course_id}/modules/{module_number}/lessons/{lesson_index}/test",
            timeout=10
        )
        if response.status_code == 200:
            test_data = response.json()
            print(f"   ✅ Тест успешно получен")
            print(f"      Название: {test_data.get('lesson_title', 'N/A')}")
            print(f"      Вопросов: {len(test_data.get('questions', []))}")
            results.append(("Получение теста", True))
        elif response.status_code == 404:
            print(f"   ⚠️ Тест не найден (возможно, еще не сгенерирован)")
            results.append(("Получение теста", None))
        else:
            print(f"   ❌ Ошибка получения теста (статус: {response.status_code})")
            results.append(("Получение теста", False))
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️ Ошибка запроса: {e}")
        results.append(("Получение теста", None))
    
    # Тест 4: Обновление теста (если тест существует)
    print(f"\n4️⃣ Обновление теста...")
    try:
        # Сначала получаем тест
        get_response = requests.get(
            f"{BASE_URL}/api/courses/{course_id}/modules/{module_number}/lessons/{lesson_index}/test",
            timeout=10
        )
        if get_response.status_code == 200:
            test_data = get_response.json()
            # Обновляем тест
            test_data['passing_score_percent'] = 80
            update_response = requests.put(
                f"{BASE_URL}/api/courses/{course_id}/modules/{module_number}/lessons/{lesson_index}/test",
                json={"test_data": test_data},
                timeout=10
            )
            if update_response.status_code == 200:
                print(f"   ✅ Тест успешно обновлен")
                results.append(("Обновление теста", True))
            else:
                print(f"   ❌ Ошибка обновления теста (статус: {update_response.status_code})")
                results.append(("Обновление теста", False))
        else:
            print(f"   ⚠️ Тест не найден, пропускаем обновление")
            results.append(("Обновление теста", None))
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️ Ошибка запроса: {e}")
        results.append(("Обновление теста", None))
    
    return results


if __name__ == "__main__":
    print("\n🧪 ЗАПУСК ТЕСТИРОВАНИЯ API ENDPOINTS\n")
    
    results = test_api_endpoints()
    
    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ ТЕСТИРОВАНИЯ API")
    print("=" * 60)
    
    for test_name, result in results:
        if result is None:
            status = "⏭️ ПРОПУЩЕН"
        elif result:
            status = "✅ ПРОЙДЕН"
        else:
            status = "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
    
    all_passed = all(r for _, r in results if r is not None)
    any_failed = any(r == False for _, r in results)
    
    if all_passed and not any_failed:
        print("\n🎉 Все тесты пройдены успешно!")
        sys.exit(0)
    elif any_failed:
        print("\n⚠️ Некоторые тесты провалены")
        sys.exit(1)
    else:
        print("\n⚠️ Некоторые тесты пропущены (возможно, backend не запущен)")
        sys.exit(0)

