"""
Извлечение реальных ID аватаров и голосов из HeyGen API
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def extract_ids():
    """Извлекает реальные ID аватаров и голосов"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        print("ERROR: HEYGEN_API_KEY not found")
        return False
    
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    print("Extracting real IDs from HeyGen API...")
    print("=" * 50)
    
    # Получаем аватары
    print("\n1. Getting avatars:")
    try:
        response = requests.get(
            'https://api.heygen.com/v2/avatars',
            headers=headers,
            timeout=10,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            avatars = data.get('data', [])
            print(f"   Found {len(avatars)} avatars")
            
            if avatars:
                first_avatar = avatars[0]
                avatar_id = first_avatar.get('avatar_id', 'N/A')
                avatar_name = first_avatar.get('name', 'No name')
                print(f"   First avatar: {avatar_id} - {avatar_name}")
                
                # Сохраняем
                with open('avatar_id.txt', 'w') as f:
                    f.write(f"{avatar_id}")
                print(f"   Saved avatar ID to avatar_id.txt")
                
                avatar_success = True
            else:
                print("   No avatars found")
                avatar_success = False
        else:
            print(f"   ERROR: {response.status_code}")
            avatar_success = False
            
    except Exception as e:
        print(f"   EXCEPTION: {e}")
        avatar_success = False
    
    # Получаем голоса
    print("\n2. Getting voices:")
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
            print(f"   Found {len(voices)} voices")
            
            if voices:
                # Ищем английский голос
                english_voices = [v for v in voices if v.get('language', '').lower() in ['english', 'en', 'multilingual']]
                
                if english_voices:
                    first_voice = english_voices[0]
                    voice_id = first_voice.get('voice_id', 'N/A')
                    voice_lang = first_voice.get('language', 'Unknown')
                    print(f"   First English voice: {voice_id} - {voice_lang}")
                    
                    # Сохраняем
                    with open('voice_id.txt', 'w') as f:
                        f.write(f"{voice_id}")
                    print(f"   Saved voice ID to voice_id.txt")
                    
                    voice_success = True
                else:
                    # Берем первый доступный голос
                    first_voice = voices[0]
                    voice_id = first_voice.get('voice_id', 'N/A')
                    voice_lang = first_voice.get('language', 'Unknown')
                    print(f"   First available voice: {voice_id} - {voice_lang}")
                    
                    # Сохраняем
                    with open('voice_id.txt', 'w') as f:
                        f.write(f"{voice_id}")
                    print(f"   Saved voice ID to voice_id.txt")
                    
                    voice_success = True
            else:
                print("   No voices found")
                voice_success = False
        else:
            print(f"   ERROR: {response.status_code}")
            voice_success = False
            
    except Exception as e:
        print(f"   EXCEPTION: {e}")
        voice_success = False
    
    return avatar_success and voice_success

def main():
    """Main function"""
    
    print("HEYGEN ID EXTRACTION")
    print("=" * 50)
    
    success = extract_ids()
    
    if success:
        print("\nSUCCESS: Extracted IDs!")
        print("Files created:")
        print("- avatar_id.txt")
        print("- voice_id.txt")
        
        print("\nNEXT STEPS:")
        print("1. Test video generation with these IDs")
        print("2. Update environment variables")
        print("3. Launch the server")
    else:
        print("\nERROR: Could not extract IDs")

if __name__ == "__main__":
    main()
