"""
Простое извлечение ID без сложного вывода
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_simple_ids():
    """Простое получение ID"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        return False
    
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    # Получаем аватары
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
            
            if isinstance(avatars, list) and avatars:
                first_avatar = avatars[0]
                if isinstance(first_avatar, dict):
                    avatar_id = first_avatar.get('avatar_id', 'N/A')
                    
                    # Сохраняем
                    with open('avatar_id.txt', 'w') as f:
                        f.write(f"{avatar_id}")
                    
                    print(f"Avatar ID: {avatar_id}")
                    return True
    except Exception as e:
        print(f"Avatar error: {e}")
    
    # Получаем голоса
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
            
            if isinstance(voices, list) and voices:
                first_voice = voices[0]
                if isinstance(first_voice, dict):
                    voice_id = first_voice.get('voice_id', 'N/A')
                    
                    # Сохраняем
                    with open('voice_id.txt', 'w') as f:
                        f.write(f"{voice_id}")
                    
                    print(f"Voice ID: {voice_id}")
                    return True
    except Exception as e:
        print(f"Voice error: {e}")
    
    return False

def main():
    """Main function"""
    
    print("Getting IDs...")
    
    success = get_simple_ids()
    
    if success:
        print("SUCCESS: Got IDs!")
        print("Files created: avatar_id.txt, voice_id.txt")
    else:
        print("ERROR: Could not get IDs")

if __name__ == "__main__":
    main()
