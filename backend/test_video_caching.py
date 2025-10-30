"""
Тест системы кэширования видео
"""
import asyncio
import json
import requests
import time

def test_video_caching():
    """Тестирует систему кэширования видео"""
    
    base_url = "http://localhost:8000"
    course_id = 3
    module_number = 1
    lesson_index = 1
    
    print("🧪 Тестирование системы кэширования видео")
    print("=" * 50)
    
    # Тестовые данные
    test_request = {
        "title": "Тестовый урок",
        "content": "Это тестовое содержимое для генерации видео",
        "avatar_id": "Abigail_expressive_2024112501",
        "voice_id": "9799f1ba6acd4b2b993fe813a18f9a91",
        "language": "ru",
        "quality": "low",
        "regenerate": False
    }
    
    # 1. Первая генерация (должна создать новое видео)
    print("1️⃣ Первая генерация видео...")
    response1 = requests.post(
        f"{base_url}/api/video/generate-lesson-cached",
        params={
            "course_id": course_id,
            "module_number": module_number,
            "lesson_index": lesson_index
        },
        json=test_request
    )
    
    if response1.status_code == 200:
        data1 = response1.json()
        print(f"✅ Первая генерация: {data1['message']}")
        print(f"   Видео ID: {data1.get('video_id', 'N/A')}")
        print(f"   Из кэша: {data1.get('is_cached', False)}")
        
        if data1.get('video_id'):
            video_id = data1['video_id']
            
            # Ждем немного для генерации
            print("⏳ Ожидание генерации...")
            time.sleep(10)
            
            # 2. Вторая генерация с тем же содержимым (должна использовать кэш)
            print("\n2️⃣ Вторая генерация с тем же содержимым...")
            response2 = requests.post(
                f"{base_url}/api/video/generate-lesson-cached",
                params={
                    "course_id": course_id,
                    "module_number": module_number,
                    "lesson_index": lesson_index
                },
                json=test_request
            )
            
            if response2.status_code == 200:
                data2 = response2.json()
                print(f"✅ Вторая генерация: {data2['message']}")
                print(f"   Видео ID: {data2.get('video_id', 'N/A')}")
                print(f"   Из кэша: {data2.get('is_cached', False)}")
                
                if data2.get('is_cached'):
                    print("🎉 Кэширование работает! Видео взято из кэша.")
                else:
                    print("⚠️ Кэширование не сработало. Создано новое видео.")
            
            # 3. Принудительная перегенерация
            print("\n3️⃣ Принудительная перегенерация...")
            test_request["regenerate"] = True
            response3 = requests.post(
                f"{base_url}/api/video/generate-lesson-cached",
                params={
                    "course_id": course_id,
                    "module_number": module_number,
                    "lesson_index": lesson_index
                },
                json=test_request
            )
            
            if response3.status_code == 200:
                data3 = response3.json()
                print(f"✅ Перегенерация: {data3['message']}")
                print(f"   Видео ID: {data3.get('video_id', 'N/A')}")
                print(f"   Из кэша: {data3.get('is_cached', False)}")
                
                if not data3.get('is_cached'):
                    print("🎉 Перегенерация работает! Создано новое видео.")
                else:
                    print("⚠️ Перегенерация не сработала. Использован кэш.")
            
            # 4. Проверка статистики кэша
            print("\n4️⃣ Статистика кэша...")
            stats_response = requests.get(f"{base_url}/api/video/cache/stats")
            
            if stats_response.status_code == 200:
                stats = stats_response.json()
                print(f"✅ Статистика кэша:")
                print(f"   Всего видео: {stats['data']['total_videos']}")
                print(f"   Завершенных: {stats['data']['completed_videos']}")
                print(f"   Неудачных: {stats['data']['failed_videos']}")
                print(f"   Генерирующихся: {stats['data']['generating_videos']}")
            
            # 5. Удаление из кэша
            print("\n5️⃣ Удаление из кэша...")
            delete_response = requests.delete(
                f"{base_url}/api/video/cache/lesson/{course_id}/{module_number}/{lesson_index}"
            )
            
            if delete_response.status_code == 200:
                delete_data = delete_response.json()
                print(f"✅ Удаление: {delete_data['message']}")
            
        else:
            print("❌ Не получен video_id в первой генерации")
    else:
        print(f"❌ Ошибка первой генерации: {response1.status_code}")
        print(response1.text)
    
    print("\n" + "=" * 50)
    print("🏁 Тест завершен")

if __name__ == "__main__":
    test_video_caching()
