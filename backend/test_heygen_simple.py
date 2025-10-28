"""
Простой тест доступных функций HeyGen API без эмодзи
"""

import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

def test_heygen_functions():
    """Тестирует доступные функции HeyGen API"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        print("ERROR: HEYGEN_API_KEY not found")
        return False
    
    # Настройка SSL
    os.environ['PYTHONHTTPSVERIFY'] = '0'
    
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    print("Testing HeyGen API functions...")
    print("=" * 40)
    
    # Тест голосов
    print("\n1. Testing voices:")
    try:
        response = requests.get(
            'https://api.heygen.com/v1/voice.list',
            headers=headers,
            timeout=10,
            verify=False
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
            
    except Exception as e:
        print(f"   EXCEPTION: {e}")
    
    # Тест аватаров
    print("\n2. Testing avatars:")
    try:
        response = requests.get(
            'https://api.heygen.com/v1/avatar.list',
            headers=headers,
            timeout=10,
            verify=False
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            avatars = data.get('data', [])
            print(f"   SUCCESS! Got {len(avatars)} avatars")
            return True
        else:
            print(f"   ERROR: {response.status_code}")
            try:
                error = response.json()
                error_code = error.get('code', 'N/A')
                error_msg = error.get('message', 'N/A')
                print(f"   Error code: {error_code}")
                print(f"   Error message: {error_msg}")
            except:
                pass
            
    except Exception as e:
        print(f"   EXCEPTION: {e}")
    
    return False

def main():
    """Main function"""
    
    print("HEYGEN API FUNCTIONALITY TEST")
    print("=" * 40)
    
    # Test functions
    success = test_heygen_functions()
    
    # Results
    print("\n" + "=" * 40)
    print("RESULTS:")
    
    if success:
        print("SUCCESS: API key is valid!")
        print("SUCCESS: Some functions are working!")
        print("\nNEXT STEPS:")
        print("1. Update API key permissions for avatars")
        print("2. Or use available voices for video creation")
        print("3. System can work with limited functionality")
    else:
        print("ERROR: API key has issues or restrictions")

if __name__ == "__main__":
    main()
