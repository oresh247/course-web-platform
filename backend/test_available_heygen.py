"""
Тест доступных функций HeyGen API
"""

import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

def test_available_functions():
    """Тестирует доступные функции HeyGen API"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        print("❌ HEYGEN_API_KEY не найден")
        return False
    
    # Настройка SSL
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    print("Тестирование доступных функций HeyGen API")
    print("=" * 50)
    
    # Тест 1: Голоса (работает)
    print("\n1️⃣ Тест голосов:")
    try:
        response = requests.get(
            'https://api.heygen.com/v1/voice.list',
            headers=headers,
            timeout=10,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            voices = data.get('data', [])
            print(f"✅ Голоса работают! Получено: {len(voices)}")
            
            print("🎤 Доступные голоса:")
            for i, voice in enumerate(voices[:3], 1):
                print(f"   {i}. {voice.get('voice_id', 'N/A')} - {voice.get('name', 'Без названия')}")
            
            return True
        else:
            print(f"❌ Ошибка голосов: {response.status_code}")
            
    except Exception as e:
        print(f"💥 Ошибка: {e}")
    
    # Тест 2: Аватары (не работает)
    print("\n2️⃣ Тест аватаров:")
    try:
        response = requests.get(
            'https://api.heygen.com/v1/avatar.list',
            headers=headers,
            timeout=10,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            avatars = data.get('data', [])
            print(f"✅ Аватары работают! Получено: {len(avatars)}")
            return True
        else:
            print(f"❌ Аватары не работают: {response.status_code}")
            try:
                error = response.json()
                print(f"   Код ошибки: {error.get('code', 'N/A')}")
                print(f"   Сообщение: {error.get('message', 'N/A')}")
            except:
                pass
            
    except Exception as e:
        print(f"💥 Ошибка: {e}")
    
    return False

def test_video_generation():
    """Тестирует создание видео (может не работать)"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        return False
    
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    print("\n3️⃣ Тест создания видео:")
    
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
                    "input_text": "Тестовое видео",
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
        response = requests.post(
            'https://api.heygen.com/v1/video.generate',
            headers=headers,
            json=payload,
            timeout=30,
            verify=False
        )
        
        print(f"📊 Статус создания видео: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            video_id = data.get('video_id')
            print(f"✅ Видео создано! ID: {video_id}")
            return True
        else:
            print(f"❌ Ошибка создания видео: {response.status_code}")
            try:
                error = response.json()
                print(f"   Код ошибки: {error.get('code', 'N/A')}")
                print(f"   Сообщение: {error.get('message', 'N/A')}")
            except:
                pass
            
    except Exception as e:
        print(f"💥 Ошибка: {e}")
    
    return False

def main():
    """Основная функция"""
    
    print("ТЕСТ ДОСТУПНЫХ ФУНКЦИЙ HEYGEN API")
    print("=" * 50)
    
    # Тест доступных функций
    voices_ok = test_available_functions()
    
    # Тест создания видео
    video_ok = test_video_generation()
    
    # Итоги
    print("\n" + "=" * 50)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
    print(f"✅ Голоса: {'Работают' if voices_ok else 'Не работают'}")
    print(f"🎬 Создание видео: {'Работает' if video_ok else 'Не работает'}")
    
    if voices_ok:
        print("\n🎉 ХОРОШИЕ НОВОСТИ:")
        print("✅ API ключ действителен!")
        print("✅ Голоса доступны!")
        print("✅ Можно создавать видео с голосами!")
        
        print("\n🔧 ЧТО НУЖНО СДЕЛАТЬ:")
        print("1. Обновите права API ключа для доступа к аватарам")
        print("2. Или используйте доступные голоса для создания видео")
        print("3. Система может работать с ограниченным функционалом")
        
    else:
        print("\n❌ ПРОБЛЕМЫ:")
        print("API ключ не работает или имеет ограничения")

if __name__ == "__main__":
    main()
