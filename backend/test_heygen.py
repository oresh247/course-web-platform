"""
Простой тест HeyGen API интеграции
"""

import requests
import os
import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("❌ python-dotenv не установлен. Установите: pip install python-dotenv")
    sys.exit(1)

def test_heygen_api():
    """Тестирует подключение к HeyGen API"""
    
    # Устанавливаем переменные для обхода SSL проблем
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        print("❌ HEYGEN_API_KEY не найден в .env файле")
        print("📝 Добавьте в .env файл:")
        print("HEYGEN_API_KEY=your_heygen_api_key_here")
        return False
    
    print(f"🔑 API ключ найден: {api_key[:10]}...")
    
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        print("🌐 Тестируем подключение к HeyGen API...")
        
        # Тест получения аватаров с отключенной проверкой SSL
        response = requests.get(
            'https://api.heygen.com/v1/avatar.list',
            headers=headers,
            timeout=10,
            verify=False  # Отключаем проверку SSL
        )
        
        if response.status_code == 200:
            data = response.json()
            avatars = data.get('data', [])
            print(f"✅ HeyGen API работает!")
            print(f"📊 Доступно аватаров: {len(avatars)}")
            
            if avatars:
                print("🎭 Примеры аватаров:")
                for i, avatar in enumerate(avatars[:3]):
                    print(f"  {i+1}. {avatar.get('avatar_id', 'N/A')} - {avatar.get('name', 'Без названия')}")
            
            return True
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"📄 Ответ: {response.text}")
            return False
            
    except requests.exceptions.SSLError as e:
        print(f"❌ SSL ошибка: {e}")
        print("🔧 Решение: Добавьте в .env файл:")
        print("PYTHONHTTPSVERIFY=0")
        return False
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Ошибка подключения: {e}")
        print("🌐 Проверьте интернет-соединение")
        return False
        
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_basic_imports():
    """Тестирует импорт основных модулей"""
    
    print("📦 Проверяем импорт модулей...")
    
    modules = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('pydantic', 'Pydantic'),
        ('requests', 'Requests'),
        ('dotenv', 'Python-dotenv')
    ]
    
    all_ok = True
    
    for module_name, display_name in modules:
        try:
            __import__(module_name)
            print(f"✅ {display_name}")
        except ImportError:
            print(f"❌ {display_name} не установлен")
            all_ok = False
    
    return all_ok

def test_simple_video_generation():
    """Тестирует простую генерацию видео"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        return False
    
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    # Простой тест создания видео
    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar",
                    "avatar_id": "default",
                    "avatar_style": "normal"
                },
                "voice": {
                    "type": "text",
                    "input_text": "Привет! Это тестовое видео.",
                    "voice_id": "default",
                    "language": "ru"
                },
                "background": {
                    "type": "color",
                    "value": "#ffffff"
                }
            }
        ],
        "dimension": {
            "width": 1920,
            "height": 1080
        },
        "aspect_ratio": "16:9",
        "quality": "high"
    }
    
    try:
        print("🎬 Тестируем создание видео...")
        
        response = requests.post(
            'https://api.heygen.com/v1/video.generate',
            headers=headers,
            json=payload,
            timeout=30,
            verify=False  # Отключаем проверку SSL
        )
        
        if response.status_code == 200:
            data = response.json()
            video_id = data.get('video_id')
            print(f"✅ Видео создано успешно!")
            print(f"🆔 ID видео: {video_id}")
            return True
        else:
            print(f"❌ Ошибка создания видео: {response.status_code}")
            print(f"📄 Ответ: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при создании видео: {e}")
        return False

def main():
    """Основная функция тестирования"""
    
    print("🧪 Тестирование HeyGen API интеграции")
    print("=" * 50)
    
    # Тест 1: Импорт модулей
    print("\n1️⃣ Тест импорта модулей:")
    imports_ok = test_basic_imports()
    
    if not imports_ok:
        print("\n❌ Не все модули установлены. Установите:")
        print("pip install fastapi uvicorn[standard] pydantic requests python-dotenv")
        return
    
    # Тест 2: HeyGen API
    print("\n2️⃣ Тест HeyGen API:")
    api_ok = test_heygen_api()
    
    if not api_ok:
        print("\n❌ HeyGen API недоступен. Проверьте:")
        print("- API ключ в .env файле")
        print("- Интернет-соединение")
        print("- Настройки корпоративной сети")
        return
    
    # Тест 3: Создание видео (опционально)
    print("\n3️⃣ Тест создания видео:")
    create_video = input("Создать тестовое видео? (y/n): ").lower().strip()
    
    if create_video == 'y':
        video_ok = test_simple_video_generation()
        if video_ok:
            print("\n🎉 Все тесты пройдены успешно!")
        else:
            print("\n⚠️ API работает, но есть проблемы с созданием видео")
    else:
        print("\n✅ Базовые тесты пройдены успешно!")
    
    print("\n🚀 Готово к работе с HeyGen API!")

if __name__ == "__main__":
    main()
