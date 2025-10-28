"""
Тест с отладкой структуры данных HeyGen API
"""

import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

def test_with_debug():
    """Тестирует HeyGen API с отладкой структуры данных"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        print("ERROR: HEYGEN_API_KEY not found")
        return False
    
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    print("Testing HeyGen API with debug...")
    print("=" * 40)
    
    # Тест аватаров
    print("\n1. Testing avatars:")
    try:
        response = requests.get(
            'https://api.heygen.com/v2/avatars',
            headers=headers,
            timeout=10,
            verify=False
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Raw data type: {type(data)}")
            print(f"   Raw data keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
            
            # Проверяем структуру
            if isinstance(data, dict):
                avatars = data.get('data', [])
                print(f"   Avatars type: {type(avatars)}")
                print(f"   Avatars length: {len(avatars) if isinstance(avatars, list) else 'Not a list'}")
                
                if isinstance(avatars, list) and avatars:
                    first_avatar = avatars[0]
                    print(f"   First avatar type: {type(first_avatar)}")
                    print(f"   First avatar: {first_avatar}")
                    
                    if isinstance(first_avatar, dict):
                        avatar_id = first_avatar.get('avatar_id', 'N/A')
                        avatar_name = first_avatar.get('name', 'No name')
                        print(f"   SUCCESS! Avatar ID: {avatar_id}")
                        print(f"   Avatar name: {avatar_name}")
                        
                        # Сохраняем
                        with open('avatar_info.txt', 'w') as f:
                            f.write(f"AVATAR_ID={avatar_id}\n")
                            f.write(f"AVATAR_NAME={avatar_name}\n")
                        
                        return True
                    else:
                        print(f"   ERROR: First avatar is not a dict: {first_avatar}")
                else:
                    print(f"   ERROR: Avatars is not a list or empty: {avatars}")
            else:
                print(f"   ERROR: Data is not a dict: {data}")
        else:
            print(f"   ERROR: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   EXCEPTION: {e}")
    
    # Тест голосов
    print("\n2. Testing voices:")
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
            print(f"   Raw data type: {type(data)}")
            print(f"   Raw data keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
            
            # Проверяем структуру
            if isinstance(data, dict):
                voices = data.get('data', [])
                print(f"   Voices type: {type(voices)}")
                print(f"   Voices length: {len(voices) if isinstance(voices, list) else 'Not a list'}")
                
                if isinstance(voices, list) and voices:
                    first_voice = voices[0]
                    print(f"   First voice type: {type(first_voice)}")
                    print(f"   First voice: {first_voice}")
                    
                    if isinstance(first_voice, dict):
                        voice_id = first_voice.get('voice_id', 'N/A')
                        voice_lang = first_voice.get('language', 'Unknown')
                        print(f"   SUCCESS! Voice ID: {voice_id}")
                        print(f"   Voice language: {voice_lang}")
                        
                        # Сохраняем
                        with open('voice_info.txt', 'w') as f:
                            f.write(f"VOICE_ID={voice_id}\n")
                            f.write(f"VOICE_LANG={voice_lang}\n")
                        
                        return True
                    else:
                        print(f"   ERROR: First voice is not a dict: {first_voice}")
                else:
                    print(f"   ERROR: Voices is not a list or empty: {voices}")
            else:
                print(f"   ERROR: Data is not a dict: {data}")
        else:
            print(f"   ERROR: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   EXCEPTION: {e}")
    
    return False

def main():
    """Main function"""
    
    print("HEYGEN API DEBUG TEST")
    print("=" * 40)
    
    success = test_with_debug()
    
    if success:
        print("\nSUCCESS: Got IDs!")
        print("Files created:")
        print("- avatar_info.txt")
        print("- voice_info.txt")
    else:
        print("\nERROR: Could not get IDs")

if __name__ == "__main__":
    main()
