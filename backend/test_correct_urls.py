"""
Простой тест с правильными URL для получения аватаров и голосов
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_correct_urls():
    """Тестирует правильные URL для HeyGen API"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        print("ERROR: HEYGEN_API_KEY not found")
        return False
    
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    print("Testing correct HeyGen URLs...")
    print("=" * 40)
    
    # Тест аватаров - правильный URL
    print("\n1. Testing avatars (correct URL):")
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
            avatars = data.get('data', [])
            print(f"   SUCCESS! Got {len(avatars)} avatars")
            
            if avatars:
                first_avatar = avatars[0]
                avatar_id = first_avatar.get('avatar_id', 'N/A')
                avatar_name = first_avatar.get('name', 'No name')
                print(f"   First avatar: {avatar_id} - {avatar_name}")
                
                # Сохраняем первый аватар
                with open('first_avatar.txt', 'w') as f:
                    f.write(f"AVATAR_ID={avatar_id}\n")
                    f.write(f"AVATAR_NAME={avatar_name}\n")
                
                print(f"   Saved to first_avatar.txt")
            
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
    
    # Тест голосов - правильный URL
    print("\n2. Testing voices (correct URL):")
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
            
            if voices:
                # Ищем английский голос
                english_voices = [v for v in voices if v.get('language', '').lower() in ['english', 'en', 'multilingual']]
                
                if english_voices:
                    first_voice = english_voices[0]
                    voice_id = first_voice.get('voice_id', 'N/A')
                    voice_lang = first_voice.get('language', 'Unknown')
                    print(f"   First English voice: {voice_id} - {voice_lang}")
                    
                    # Сохраняем первый голос
                    with open('first_voice.txt', 'w') as f:
                        f.write(f"VOICE_ID={voice_id}\n")
                        f.write(f"VOICE_LANG={voice_lang}\n")
                    
                    print(f"   Saved to first_voice.txt")
                else:
                    print("   No English voices found")
            
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
    
    print("CORRECT HEYGEN URLS TEST")
    print("=" * 40)
    
    success = test_correct_urls()
    
    if success:
        print("\nSUCCESS: Got real avatar and voice IDs!")
        print("Files created:")
        print("- first_avatar.txt")
        print("- first_voice.txt")
        
        print("\nNEXT STEPS:")
        print("1. Test video generation with these IDs")
        print("2. Update environment variables")
        print("3. Launch the server")
    else:
        print("\nERROR: Could not get IDs")

if __name__ == "__main__":
    main()
