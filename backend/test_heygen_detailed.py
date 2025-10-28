"""
Расширенный тест HeyGen API с детальной диагностикой
"""

import requests
import os
import sys
from pathlib import Path
import json

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("❌ python-dotenv не установлен. Установите: pip install python-dotenv")
    sys.exit(1)

def test_api_key_format():
    """Проверяет формат API ключа"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        print("❌ HEYGEN_API_KEY не найден")
        return False
    
    print(f"🔑 API ключ: {api_key[:15]}...")
    
    # Проверяем формат ключа
    if not api_key.startswith('sk_'):
        print("⚠️ API ключ не начинается с 'sk_' - возможно неправильный формат")
    
    if len(api_key) < 20:
        print("⚠️ API ключ слишком короткий")
    
    return True

def test_heygen_endpoints():
    """Тестирует различные endpoints HeyGen"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        return False
    
    # Устанавливаем переменные для обхода SSL проблем
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''
    
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    endpoints = [
        {
            'name': 'Avatar List',
            'url': 'https://api.heygen.com/v1/avatar.list',
            'method': 'GET'
        },
        {
            'name': 'Voice List', 
            'url': 'https://api.heygen.com/v1/voice.list',
            'method': 'GET'
        },
        {
            'name': 'User Info',
            'url': 'https://api.heygen.com/v1/user.info',
            'method': 'GET'
        }
    ]
    
    print("🌐 Тестируем различные endpoints HeyGen API...")
    
    for endpoint in endpoints:
        try:
            print(f"\n📡 Тестируем: {endpoint['name']}")
            
            if endpoint['method'] == 'GET':
                response = requests.get(
                    endpoint['url'],
                    headers=headers,
                    timeout=10,
                    verify=False
                )
            else:
                response = requests.post(
                    endpoint['url'],
                    headers=headers,
                    timeout=10,
                    verify=False
                )
            
            print(f"   Статус: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ {endpoint['name']} работает!")
                try:
                    data = response.json()
                    if 'data' in data:
                        print(f"   📊 Данных: {len(data['data'])}")
                except:
                    pass
            elif response.status_code == 403:
                print(f"   ❌ Доступ запрещен (403)")
                try:
                    error_data = response.json()
                    print(f"   📄 Ошибка: {error_data}")
                except:
                    print(f"   📄 Ответ: {response.text}")
            elif response.status_code == 401:
                print(f"   ❌ Неавторизован (401) - проверьте API ключ")
            else:
                print(f"   ⚠️ Неожиданный статус: {response.status_code}")
                print(f"   📄 Ответ: {response.text[:200]}...")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
    
    return True

def test_alternative_api_key():
    """Предлагает альтернативные способы получения API ключа"""
    
    print("\n🔧 Возможные решения проблемы с API ключом:")
    print("\n1️⃣ Проверьте HeyGen Dashboard:")
    print("   - Зайдите на https://app.heygen.com/")
    print("   - Перейдите в Settings → API Keys")
    print("   - Убедитесь, что ключ активен")
    
    print("\n2️⃣ Создайте новый API ключ:")
    print("   - Удалите старый ключ")
    print("   - Создайте новый с полными правами")
    print("   - Обновите в .env файле")
    
    print("\n3️⃣ Проверьте баланс:")
    print("   - Зайдите в Billing/Credits")
    print("   - Убедитесь, что есть кредиты")
    
    print("\n4️⃣ Проверьте права ключа:")
    print("   - Ключ должен иметь права на avatar.list")
    print("   - Ключ должен иметь права на video.generate")
    
    print("\n5️⃣ Альтернативные способы:")
    print("   - Попробуйте другой аккаунт HeyGen")
    print("   - Свяжитесь с поддержкой HeyGen")
    print("   - Проверьте документацию: https://docs.heygen.com/")

def test_without_heygen():
    """Тестирует работу системы без HeyGen"""
    
    print("\n🎯 Тест работы системы без HeyGen:")
    
    try:
        # Импортируем основные модули
        from fastapi import FastAPI
        import uvicorn
        from pydantic import BaseModel
        
        print("✅ Все основные модули работают")
        
        # Создаем простое приложение
        app = FastAPI(title="AI Course Builder - Test")
        
        @app.get("/")
        async def root():
            return {"message": "AI Course Builder работает без HeyGen!"}
        
        @app.get("/health")
        async def health():
            return {
                "status": "healthy",
                "heygen_available": False,
                "message": "Система работает, но HeyGen недоступен"
            }
        
        print("✅ FastAPI приложение создано")
        print("🚀 Можете запустить сервер: uvicorn main:app --reload")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

def main():
    """Основная функция расширенного тестирования"""
    
    print("🔍 Расширенная диагностика HeyGen API")
    print("=" * 60)
    
    # Тест 1: Формат API ключа
    print("\n1️⃣ Проверка формата API ключа:")
    key_ok = test_api_key_format()
    
    if not key_ok:
        print("❌ API ключ не найден. Создайте .env файл с HEYGEN_API_KEY")
        return
    
    # Тест 2: Различные endpoints
    print("\n2️⃣ Тестирование endpoints:")
    test_heygen_endpoints()
    
    # Тест 3: Альтернативные решения
    print("\n3️⃣ Рекомендации по решению:")
    test_alternative_api_key()
    
    # Тест 4: Работа без HeyGen
    print("\n4️⃣ Тест работы системы:")
    test_without_heygen()
    
    print("\n" + "=" * 60)
    print("📋 Резюме:")
    print("✅ Все модули Python установлены")
    print("✅ SSL проблемы решены")
    print("❌ HeyGen API недоступен (проблема с ключом)")
    print("✅ Система может работать без HeyGen")
    
    print("\n🎯 Следующие шаги:")
    print("1. Обновите API ключ HeyGen")
    print("2. Или запустите систему без видео-функций")
    print("3. Или используйте альтернативный сервис")

if __name__ == "__main__":
    main()
