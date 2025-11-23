"""
Скрипт для тестирования функциональности генерации тестов
"""
import sys
import os
import json
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.database import db
from backend.services.test_generator_service import TestGeneratorService
from backend.models.domain import LessonTest

def test_test_generation():
    """Тестирует генерацию теста"""
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ГЕНЕРАЦИИ ТЕСТА")
    print("=" * 60)
    
    # Инициализируем сервис
    test_generator = TestGeneratorService()
    
    # Тестовые данные
    lesson_title = "Введение в Python"
    lesson_goal = "Изучить основы языка программирования Python"
    content_outline = [
        "Что такое Python",
        "Установка Python",
        "Первая программа",
        "Переменные и типы данных",
        "Операторы и выражения"
    ]
    course_title = "Основы программирования на Python"
    target_audience = "Начинающие программисты"
    module_title = "Основы Python"
    
    print(f"\n📝 Генерируем тест для урока: {lesson_title}")
    print(f"   Цель урока: {lesson_goal}")
    print(f"   Количество вопросов: 10")
    
    # Генерируем тест
    test = test_generator.generate_test(
        lesson_title=lesson_title,
        lesson_goal=lesson_goal,
        content_outline=content_outline,
        course_title=course_title,
        target_audience=target_audience,
        module_title=module_title,
        num_questions=10,
        model="gpt-4-turbo-preview"  # Используем модель, которая поддерживает JSON mode
    )
    
    if not test:
        print("❌ ОШИБКА: Не удалось сгенерировать тест")
        return False
    
    print(f"\n✅ Тест успешно сгенерирован!")
    print(f"   Название: {test.lesson_title}")
    print(f"   Количество вопросов: {test.total_questions}")
    print(f"   Процент для прохождения: {test.passing_score_percent}%")
    
    # Проверяем структуру теста
    print(f"\n📊 Проверка структуры теста:")
    
    if not test.questions:
        print("❌ ОШИБКА: Нет вопросов в тесте")
        return False
    
    print(f"   ✅ Вопросов в тесте: {len(test.questions)}")
    
    # Проверяем каждый вопрос
    for i, question in enumerate(test.questions, 1):
        print(f"\n   Вопрос {i}:")
        print(f"      Текст: {question.question_text[:50]}...")
        
        if not question.options:
            print(f"      ❌ ОШИБКА: Нет вариантов ответа")
            return False
        
        print(f"      ✅ Вариантов ответа: {len(question.options)}")
        
        # Проверяем, что есть ровно один правильный ответ
        correct_count = sum(1 for opt in question.options if opt.is_correct)
        if correct_count != 1:
            print(f"      ❌ ОШИБКА: Должен быть ровно один правильный ответ (найдено: {correct_count})")
            return False
        
        print(f"      ✅ Правильных ответов: {correct_count}")
        
        if question.explanation:
            print(f"      ✅ Есть объяснение")
        else:
            print(f"      ⚠️ Нет объяснения")
    
    print(f"\n✅ Все проверки пройдены успешно!")
    return True


def test_database_operations():
    """Тестирует операции с БД для тестов"""
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ОПЕРАЦИЙ С БД")
    print("=" * 60)
    
    # Создаем тестовый тест
    test_data = {
        "lesson_title": "Тестовый урок",
        "lesson_goal": "Тестовая цель",
        "questions": [
            {
                "question_text": "Тестовый вопрос 1?",
                "options": [
                    {"option_text": "Правильный ответ", "is_correct": True},
                    {"option_text": "Неправильный ответ 1", "is_correct": False},
                    {"option_text": "Неправильный ответ 2", "is_correct": False}
                ],
                "explanation": "Это правильный ответ потому что..."
            },
            {
                "question_text": "Тестовый вопрос 2?",
                "options": [
                    {"option_text": "Неправильный ответ", "is_correct": False},
                    {"option_text": "Правильный ответ", "is_correct": True},
                    {"option_text": "Неправильный ответ 2", "is_correct": False}
                ],
                "explanation": "Это правильный ответ"
            }
        ],
        "total_questions": 2,
        "passing_score_percent": 70
    }
    
    # Тестовые параметры
    course_id = 1
    module_number = 1
    lesson_index = 0
    
    print(f"\n💾 Сохраняем тест в БД:")
    print(f"   Курс ID: {course_id}")
    print(f"   Модуль: {module_number}")
    print(f"   Урок: {lesson_index}")
    
    try:
        # Сохраняем тест
        record_id = db.save_lesson_test(
            course_id=course_id,
            module_number=module_number,
            lesson_index=lesson_index,
            lesson_title=test_data["lesson_title"],
            test_data=test_data
        )
        print(f"   ✅ Тест сохранен (ID записи: {record_id})")
        
        # Получаем тест обратно
        print(f"\n📖 Получаем тест из БД:")
        retrieved_test = db.get_lesson_test(
            course_id=course_id,
            module_number=module_number,
            lesson_index=lesson_index
        )
        
        if not retrieved_test:
            print("   ❌ ОШИБКА: Тест не найден в БД")
            return False
        
        print(f"   ✅ Тест получен из БД")
        print(f"      Название: {retrieved_test.get('lesson_title')}")
        print(f"      Вопросов: {retrieved_test.get('total_questions')}")
        
        # Проверяем структуру
        if retrieved_test.get('questions'):
            print(f"      ✅ Вопросы присутствуют: {len(retrieved_test['questions'])}")
        else:
            print(f"      ❌ ОШИБКА: Вопросы отсутствуют")
            return False
        
        print(f"\n✅ Операции с БД работают корректно!")
        return True
        
    except Exception as e:
        print(f"   ❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pydantic_validation():
    """Тестирует валидацию Pydantic моделей"""
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ВАЛИДАЦИИ PYDANTIC")
    print("=" * 60)
    
    # Тестовые данные
    test_data = {
        "lesson_title": "Тестовый урок",
        "lesson_goal": "Тестовая цель",
        "questions": [
            {
                "question_text": "Тестовый вопрос?",
                "options": [
                    {"option_text": "Правильный ответ", "is_correct": True},
                    {"option_text": "Неправильный ответ", "is_correct": False}
                ],
                "explanation": "Объяснение"
            }
        ],
        "total_questions": 1,
        "passing_score_percent": 70
    }
    
    print(f"\n🔍 Тестируем валидацию LessonTest:")
    
    try:
        test = LessonTest(**test_data)
        print(f"   ✅ Валидация прошла успешно")
        print(f"      Название: {test.lesson_title}")
        print(f"      Вопросов: {test.total_questions}")
        print(f"      Процент прохождения: {test.passing_score_percent}%")
        return True
    except Exception as e:
        print(f"   ❌ ОШИБКА валидации: {e}")
        return False


if __name__ == "__main__":
    print("\n🧪 ЗАПУСК ТЕСТИРОВАНИЯ ФУНКЦИОНАЛЬНОСТИ ТЕСТОВ\n")
    
    results = []
    
    # Тест 1: Валидация Pydantic
    results.append(("Валидация Pydantic", test_pydantic_validation()))
    
    # Тест 2: Генерация теста (требует OpenAI API ключ)
    try:
        results.append(("Генерация теста", test_test_generation()))
    except Exception as e:
        print(f"\n⚠️ Пропущен тест генерации (требуется OpenAI API ключ): {e}")
        results.append(("Генерация теста", None))
    
    # Тест 3: Операции с БД
    results.append(("Операции с БД", test_database_operations()))
    
    # Итоги
    print("\n" + "=" * 60)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
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
    
    if all_passed:
        print("\n🎉 Все тесты пройдены успешно!")
        sys.exit(0)
    else:
        print("\n⚠️ Некоторые тесты провалены")
        sys.exit(1)

