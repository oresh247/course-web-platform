"""
Простой тест различных вариантов HeyGen API
"""

import requests
import os
import json

def test_api_key_variations():
    """Тестирует различные варианты API ключей"""
    
    # Получаем текущий ключ
    current_key = os.getenv('HEYGEN_API_KEY')
    if not current_key:
        print("❌ HEYGEN_API_KEY не найден в .env")
        return
    
    print(f"🔑 Текущий ключ: {current_key}")
    
    # Настройка SSL
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    
    # Различные варианты тестирования
    test_cases = [
        {
            'name': 'Текущий ключ',
            'key': current_key,
            'headers': {'X-API-KEY': current_key}
        },
        {
            'name': 'Ключ без пробелов',
            'key': current_key.strip(),
            'headers': {'X-API-KEY': current_key.strip()}
        },
        {
            'name': 'Ключ в Authorization',
            'key': current_key,
            'headers': {'Authorization': f'Bearer {current_key}'}
        },
        {
            'name': 'Ключ в API-Key',
            'key': current_key,
            'headers': {'API-Key': current_key}
        }
    ]
    
    print("\n🧪 Тестирование различных вариантов:")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}️⃣ {test_case['name']}")
        print(f"   Ключ: {test_case['key'][:15]}...")
        
        try:
            response = requests.get(
                'https://api.heygen.com/v1/avatar.list',
                headers=test_case['headers'],
                timeout=10,
                verify=False
            )
            
            print(f"   📊 Статус: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ УСПЕХ!")
                try:
                    data = response.json()
                    avatars_count = len(data.get('data', []))
                    print(f"   📈 Аватаров: {avatars_count}")
                    return True
                except:
                    pass
            elif response.status_code == 403:
                print(f"   ❌ Доступ запрещен")
                try:
                    error = response.json()
                    print(f"   🔍 Ошибка: {error.get('message', 'N/A')}")
                except:
                    pass
            else:
                print(f"   ⚠️ Статус: {response.status_code}")
                
        except Exception as e:
            print(f"   💥 Ошибка: {e}")
    
    return False

def test_simple_request():
    """Простой тест запроса"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        return False
    
    print("\n🎯 Простой тест запроса:")
    print("=" * 30)
    
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        print("📡 Отправляем запрос к avatar.list...")
        
        response = requests.get(
            'https://api.heygen.com/v1/avatar.list',
            headers=headers,
            timeout=15,
            verify=False
        )
        
        print(f"📊 Статус ответа: {response.status_code}")
        print(f"⏱️ Время ответа: {response.elapsed.total_seconds():.2f}s")
        print(f"📏 Размер ответа: {len(response.text)} символов")
        
        if response.status_code == 200:
            print("✅ Запрос успешен!")
            try:
                data = response.json()
                print(f"📈 Получено аватаров: {len(data.get('data', []))}")
                return True
            except Exception as e:
                print(f"⚠️ Ошибка парсинга JSON: {e}")
                print(f"📄 Первые 200 символов ответа:")
                print(response.text[:200])
        else:
            print(f"❌ Ошибка запроса: {response.status_code}")
            print(f"📄 Ответ сервера:")
            print(response.text)
            
    except Exception as e:
        print(f"💥 Исключение: {e}")
    
    return False

def main():
    """Основная функция"""
    
    print("🔍 ПРОСТОЙ ТЕСТ HEYGEN API")
    print("=" * 40)
    
    # Простой тест
    simple_ok = test_simple_request()
    
    if simple_ok:
        print("\n🎉 API работает! Проблема решена!")
        return
    
    # Тест различных вариантов
    print("\n🔧 Пробуем различные варианты...")
    variations_ok = test_api_key_variations()
    
    if variations_ok:
        print("\n🎉 Найден рабочий вариант!")
    else:
        print("\n❌ Все варианты не работают")
        print("\n🔧 РЕКОМЕНДАЦИИ:")
        print("1. Проверьте API ключ на https://app.heygen.com/")
        print("2. Создайте новый ключ с полными правами")
        print("3. Убедитесь в наличии кредитов")
        print("4. Проверьте интернет-соединение")

if __name__ == "__main__":
    main()
