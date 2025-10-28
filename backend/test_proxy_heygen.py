"""
Настройка прокси для HeyGen API в корпоративной сети
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_with_proxy_settings():
    """Тестирует HeyGen API с настройками прокси"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        print("❌ HEYGEN_API_KEY не найден")
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
    
    # Различные настройки прокси
    proxy_configs = [
        {
            'name': 'Без прокси',
            'proxies': None
        },
        {
            'name': 'Системный прокси',
            'proxies': {
                'http': os.getenv('HTTP_PROXY', ''),
                'https': os.getenv('HTTPS_PROXY', '')
            }
        },
        {
            'name': 'Прямое соединение',
            'proxies': {
                'http': '',
                'https': ''
            }
        }
    ]
    
    print("🌐 Тестирование с различными настройками прокси:")
    print("=" * 60)
    
    for config in proxy_configs:
        print(f"\n🧪 {config['name']}:")
        
        try:
            response = requests.get(
                'https://api.heygen.com/v1/avatar.list',
                headers=headers,
                proxies=config['proxies'],
                timeout=30,
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
                    print(f"   🔍 Код: {error.get('code', 'N/A')}")
                    print(f"   📝 Сообщение: {error.get('message', 'N/A')}")
                except:
                    pass
            else:
                print(f"   ⚠️ Статус: {response.status_code}")
                
        except requests.exceptions.ProxyError as e:
            print(f"   🔌 Ошибка прокси: {str(e)[:100]}...")
        except requests.exceptions.Timeout as e:
            print(f"   ⏰ Таймаут: {e}")
        except Exception as e:
            print(f"   💥 Ошибка: {str(e)[:100]}...")
    
    return False

def test_alternative_endpoints():
    """Тестирует альтернативные endpoints HeyGen"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        return False
    
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    # Альтернативные endpoints
    endpoints = [
        'https://api.heygen.com/v1/avatar.list',
        'https://api.heygen.com/v2/avatar.list',
        'https://api.heygen.com/avatar.list',
        'https://heygen-api.com/v1/avatar.list'
    ]
    
    print("\n🔗 Тестирование альтернативных endpoints:")
    print("=" * 50)
    
    for endpoint in endpoints:
        print(f"\n📡 {endpoint}")
        
        try:
            response = requests.get(
                endpoint,
                headers=headers,
                timeout=15,
                verify=False
            )
            
            print(f"   📊 Статус: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ РАБОТАЕТ!")
                return True
            elif response.status_code == 403:
                print(f"   ❌ Доступ запрещен")
            else:
                print(f"   ⚠️ Статус: {response.status_code}")
                
        except Exception as e:
            print(f"   💥 Ошибка: {str(e)[:80]}...")
    
    return False

def main():
    """Основная функция"""
    
    print("🔧 НАСТРОЙКА ПРОКСИ ДЛЯ HEYGEN API")
    print("=" * 50)
    
    # Тест 1: Настройки прокси
    proxy_ok = test_with_proxy_settings()
    
    if proxy_ok:
        print("\n🎉 Проблема решена! Найдена рабочая конфигурация прокси")
        return
    
    # Тест 2: Альтернативные endpoints
    endpoints_ok = test_alternative_endpoints()
    
    if endpoints_ok:
        print("\n🎉 Найден альтернативный endpoint!")
        return
    
    # Рекомендации
    print("\n" + "=" * 50)
    print("🎯 РЕКОМЕНДАЦИИ ДЛЯ КОРПОРАТИВНОЙ СЕТИ:")
    print("\n1️⃣ Обратитесь к IT-отделу:")
    print("   - Запросите доступ к api.heygen.com")
    print("   - Уточните настройки прокси для внешних API")
    print("   - Проверьте whitelist доменов")
    
    print("\n2️⃣ Альтернативные решения:")
    print("   - Используйте мобильный интернет (hotspot)")
    print("   - Попробуйте с другого компьютера/сети")
    print("   - Используйте VPN для обхода корпоративных ограничений")
    
    print("\n3️⃣ Временное решение:")
    print("   - Используйте мок-сервис для разработки")
    print("   - Тестируйте на домашней сети")
    print("   - Настройте CI/CD на внешнем сервере")

if __name__ == "__main__":
    main()
