"""
Детальная отладка HeyGen API без мок-сервиса
"""

import requests
import os
import sys
import json
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

def debug_api_key():
    """Детальная отладка API ключа"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        print("❌ HEYGEN_API_KEY не найден в .env файле")
        return False
    
    print(f"🔑 API ключ: {api_key}")
    print(f"📏 Длина ключа: {len(api_key)} символов")
    print(f"🔤 Начинается с: {api_key[:5]}...")
    
    # Проверяем формат
    if not api_key.startswith('sk_'):
        print("⚠️ ВНИМАНИЕ: Ключ не начинается с 'sk_'")
        print("   Возможно, это неправильный формат ключа")
    
    return True

def debug_heygen_endpoints():
    """Детальная отладка всех endpoints HeyGen"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        return False
    
    # Настройка SSL
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    os.environ['CURL_CA_BUNDLE'] = ''
    os.environ['REQUESTS_CA_BUNDLE'] = ''
    
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json',
        'User-Agent': 'AI-Course-Builder/1.0'
    }
    
    # Список всех возможных endpoints
    endpoints = [
        {
            'name': 'Avatar List',
            'url': 'https://api.heygen.com/v1/avatar.list',
            'method': 'GET',
            'description': 'Получение списка аватаров'
        },
        {
            'name': 'Voice List',
            'url': 'https://api.heygen.com/v1/voice.list', 
            'method': 'GET',
            'description': 'Получение списка голосов'
        },
        {
            'name': 'User Info',
            'url': 'https://api.heygen.com/v1/user.info',
            'method': 'GET',
            'description': 'Информация о пользователе'
        },
        {
            'name': 'Avatar List (альтернативный)',
            'url': 'https://api.heygen.com/v1/avatars',
            'method': 'GET',
            'description': 'Альтернативный endpoint для аватаров'
        },
        {
            'name': 'Voice List (альтернативный)',
            'url': 'https://api.heygen.com/v1/voices',
            'method': 'GET',
            'description': 'Альтернативный endpoint для голосов'
        }
    ]
    
    print("🌐 Детальная отладка HeyGen API endpoints:")
    print("=" * 60)
    
    working_endpoints = []
    failed_endpoints = []
    
    for i, endpoint in enumerate(endpoints, 1):
        print(f"\n{i}️⃣ {endpoint['name']}")
        print(f"   📡 URL: {endpoint['url']}")
        print(f"   📝 Описание: {endpoint['description']}")
        
        try:
            if endpoint['method'] == 'GET':
                response = requests.get(
                    endpoint['url'],
                    headers=headers,
                    timeout=15,
                    verify=False
                )
            else:
                response = requests.post(
                    endpoint['url'],
                    headers=headers,
                    timeout=15,
                    verify=False
                )
            
            print(f"   📊 Статус: {response.status_code}")
            print(f"   ⏱️ Время ответа: {response.elapsed.total_seconds():.2f}s")
            
            # Анализируем ответ
            if response.status_code == 200:
                print(f"   ✅ УСПЕХ!")
                try:
                    data = response.json()
                    if 'data' in data:
                        print(f"   📈 Данных получено: {len(data['data'])}")
                    if 'total' in data:
                        print(f"   📊 Всего записей: {data['total']}")
                except:
                    print(f"   📄 Ответ: {response.text[:100]}...")
                working_endpoints.append(endpoint)
                
            elif response.status_code == 403:
                print(f"   ❌ ДОСТУП ЗАПРЕЩЕН (403)")
                try:
                    error_data = response.json()
                    print(f"   🔍 Код ошибки: {error_data.get('code', 'N/A')}")
                    print(f"   📝 Сообщение: {error_data.get('message', 'N/A')}")
                except:
                    print(f"   📄 Ответ: {response.text}")
                failed_endpoints.append(endpoint)
                
            elif response.status_code == 401:
                print(f"   ❌ НЕАВТОРИЗОВАН (401)")
                print(f"   🔑 Проблема с API ключом")
                failed_endpoints.append(endpoint)
                
            elif response.status_code == 404:
                print(f"   ❌ НЕ НАЙДЕН (404)")
                print(f"   🔗 Endpoint не существует")
                failed_endpoints.append(endpoint)
                
            else:
                print(f"   ⚠️ Неожиданный статус: {response.status_code}")
                print(f"   📄 Ответ: {response.text[:200]}...")
                failed_endpoints.append(endpoint)
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ ТАЙМАУТ - сервер не отвечает")
            failed_endpoints.append(endpoint)
            
        except requests.exceptions.ConnectionError as e:
            print(f"   🔌 ОШИБКА ПОДКЛЮЧЕНИЯ: {e}")
            failed_endpoints.append(endpoint)
            
        except Exception as e:
            print(f"   💥 НЕОЖИДАННАЯ ОШИБКА: {e}")
            failed_endpoints.append(endpoint)
    
    # Итоговая статистика
    print("\n" + "=" * 60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА:")
    print(f"✅ Работающих endpoints: {len(working_endpoints)}")
    print(f"❌ Не работающих endpoints: {len(failed_endpoints)}")
    
    if working_endpoints:
        print("\n✅ РАБОТАЮЩИЕ ENDPOINTS:")
        for endpoint in working_endpoints:
            print(f"   - {endpoint['name']}: {endpoint['url']}")
    
    if failed_endpoints:
        print("\n❌ НЕ РАБОТАЮЩИЕ ENDPOINTS:")
        for endpoint in failed_endpoints:
            print(f"   - {endpoint['name']}: {endpoint['url']}")
    
    return len(working_endpoints) > 0

def debug_api_key_permissions():
    """Отладка прав API ключа"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        return False
    
    print("\n🔐 ОТЛАДКА ПРАВ API КЛЮЧА:")
    print("=" * 40)
    
    # Проверяем различные комбинации заголовков
    header_variations = [
        {
            'name': 'Стандартные заголовки',
            'headers': {
                'X-API-KEY': api_key,
                'Content-Type': 'application/json'
            }
        },
        {
            'name': 'С Authorization заголовком',
            'headers': {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
        },
        {
            'name': 'С API-Key заголовком',
            'headers': {
                'API-Key': api_key,
                'Content-Type': 'application/json'
            }
        },
        {
            'name': 'Минимальные заголовки',
            'headers': {
                'X-API-KEY': api_key
            }
        }
    ]
    
    for variation in header_variations:
        print(f"\n🧪 Тест: {variation['name']}")
        
        try:
            response = requests.get(
                'https://api.heygen.com/v1/avatar.list',
                headers=variation['headers'],
                timeout=10,
                verify=False
            )
            
            print(f"   📊 Статус: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ УСПЕХ! Этот вариант заголовков работает!")
                return True
            elif response.status_code == 403:
                print(f"   ❌ Доступ запрещен")
            elif response.status_code == 401:
                print(f"   ❌ Неавторизован")
            else:
                print(f"   ⚠️ Статус: {response.status_code}")
                
        except Exception as e:
            print(f"   💥 Ошибка: {e}")
    
    return False

def debug_heygen_documentation():
    """Проверка актуальности документации HeyGen"""
    
    print("\n📚 ПРОВЕРКА ДОКУМЕНТАЦИИ HEYGEN:")
    print("=" * 40)
    
    # Проверяем доступность документации
    doc_urls = [
        'https://docs.heygen.com/',
        'https://api.heygen.com/docs',
        'https://heygen.com/api-docs'
    ]
    
    for url in doc_urls:
        try:
            response = requests.get(url, timeout=10, verify=False)
            print(f"📖 {url}: {response.status_code}")
        except Exception as e:
            print(f"❌ {url}: {e}")

def main():
    """Основная функция отладки"""
    
    print("🔍 ДЕТАЛЬНАЯ ОТЛАДКА HEYGEN API")
    print("=" * 60)
    
    # Отладка 1: API ключ
    print("\n1️⃣ ОТЛАДКА API КЛЮЧА:")
    key_ok = debug_api_key()
    
    if not key_ok:
        print("❌ API ключ не найден. Создайте .env файл с HEYGEN_API_KEY")
        return
    
    # Отладка 2: Endpoints
    print("\n2️⃣ ОТЛАДКА ENDPOINTS:")
    endpoints_ok = debug_heygen_endpoints()
    
    # Отладка 3: Права ключа
    print("\n3️⃣ ОТЛАДКА ПРАВ КЛЮЧА:")
    permissions_ok = debug_api_key_permissions()
    
    # Отладка 4: Документация
    print("\n4️⃣ ПРОВЕРКА ДОКУМЕНТАЦИИ:")
    debug_heygen_documentation()
    
    # Итоговые рекомендации
    print("\n" + "=" * 60)
    print("🎯 РЕКОМЕНДАЦИИ ПО ИСПРАВЛЕНИЮ:")
    
    if not endpoints_ok and not permissions_ok:
        print("\n❌ ПРОБЛЕМА: API ключ недействителен или не имеет прав")
        print("\n🔧 РЕШЕНИЯ:")
        print("1. Зайдите на https://app.heygen.com/")
        print("2. Перейдите в Settings → API Keys")
        print("3. Удалите старый ключ и создайте новый")
        print("4. Убедитесь, что ключ имеет права на:")
        print("   - avatar.list")
        print("   - voice.list") 
        print("   - video.generate")
        print("5. Проверьте баланс кредитов")
        print("6. Обновите ключ в .env файле")
        
    elif endpoints_ok:
        print("\n✅ API работает! Проблема была временной")
        print("🚀 Можете использовать систему")
        
    else:
        print("\n⚠️ Частичные проблемы с API")
        print("🔧 Попробуйте обновить API ключ")

if __name__ == "__main__":
    main()
