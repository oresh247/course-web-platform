"""
Правильный тест HeyGen API с официальными endpoints
"""

import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

def test_heygen_api_correct():
    """Тестирует HeyGen API с правильными endpoints"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        print("ERROR: HEYGEN_API_KEY not found")
        return False
    
    # Правильные заголовки
    headers = {
        'X-Api-Key': api_key,  # Правильный заголовок
        'Content-Type': 'application/json'
    }
    
    print("Testing HeyGen API with correct endpoints...")
    print("=" * 50)
    
    # Тест 1: Проверка аутентификации
    print("\n1. Testing authentication (user/me):")
    try:
        response = requests.get(
            'https://api.heygen.com/v1/user/me',
            headers=headers,
            timeout=10
            # НЕ отключаем verify - используем правильный домен
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   SUCCESS! User authenticated")
            print(f"   User info: {data}")
            return True
        else:
            print(f"   ERROR: {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error}")
            except:
                print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   EXCEPTION: {e}")
    
    # Тест 2: Список аватаров (V2)
    print("\n2. Testing avatars (V2):")
    try:
        response = requests.get(
            'https://api.heygen.com/v2/avatars',
            headers=headers,
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            avatars = data.get('data', [])
            print(f"   SUCCESS! Got {len(avatars)} avatars")
            
            print("   Available avatars:")
            for i, avatar in enumerate(avatars[:3], 1):
                avatar_id = avatar.get('avatar_id', 'N/A')
                avatar_name = avatar.get('name', 'No name')
                print(f"     {i}. {avatar_id} - {avatar_name}")
            
            return True
        else:
            print(f"   ERROR: {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error}")
            except:
                print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   EXCEPTION: {e}")
    
    # Тест 3: Список голосов
    print("\n3. Testing voices:")
    try:
        response = requests.get(
            'https://api.heygen.com/v1/voice.list',
            headers=headers,
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            voices = data.get('data', [])
            print(f"   SUCCESS! Got {len(voices)} voices")
            
            print("   Available voices:")
            for i, voice in enumerate(voices[:3], 1):
                voice_id = voice.get('voice_id', 'N/A')
                voice_name = voice.get('name', 'No name')
                print(f"     {i}. {voice_id} - {voice_name}")
            
            return True
        else:
            print(f"   ERROR: {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error}")
            except:
                print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   EXCEPTION: {e}")
    
    return False

def test_video_generation_v2():
    """Тестирует создание видео через V2 API"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        return False
    
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    print("\n4. Testing video generation (V2):")
    
    # Правильный payload для V2 API
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
                    "input_text": "Hello! This is a test video.",
                    "voice_id": "default",
                    "language": "en"
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
            'https://api.heygen.com/v2/video/generate',
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            video_id = data.get('video_id')
            print(f"   SUCCESS! Video created! ID: {video_id}")
            return True
        else:
            print(f"   ERROR: {response.status_code}")
            try:
                error = response.json()
                print(f"   Error: {error}")
            except:
                print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   EXCEPTION: {e}")
    
    return False

def main():
    """Main function"""
    
    print("HEYGEN API CORRECT ENDPOINTS TEST")
    print("=" * 50)
    
    # Test with correct endpoints
    auth_ok = test_heygen_api_correct()
    
    # Test video generation
    video_ok = test_video_generation_v2()
    
    # Results
    print("\n" + "=" * 50)
    print("RESULTS:")
    
    if auth_ok:
        print("SUCCESS: API key is valid!")
        print("SUCCESS: Correct endpoints are working!")
        
        if video_ok:
            print("SUCCESS: Video generation is working!")
        else:
            print("WARNING: Video generation needs testing")
        
        print("\nNEXT STEPS:")
        print("1. Update HeyGen service to use correct endpoints")
        print("2. Use X-Api-Key header instead of X-API-KEY")
        print("3. Remove verify=False - use proper domain")
        print("4. Test video generation functionality")
        
    else:
        print("ERROR: API key or endpoints still have issues")
        print("\nTROUBLESHOOTING:")
        print("1. Check API key format and permissions")
        print("2. Verify network connectivity to api.heygen.com")
        print("3. Check HeyGen documentation for latest endpoints")

if __name__ == "__main__":
    main()
