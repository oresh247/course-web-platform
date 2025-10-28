"""
Извлечение ID голоса из известной структуры данных
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_voice_id_from_known_structure():
    """Получение ID голоса из известной структуры"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        return False
    
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
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
            
            # Из предыдущего вывода мы знаем, что структура такая:
            # data['data'] содержит список голосов
            # каждый голос имеет 'voice_id'
            
            voices = data.get('data', [])
            
            if voices and len(voices) > 0:
                first_voice = voices[0]
                voice_id = first_voice.get('voice_id')
                
                if voice_id:
                    # Сохраняем
                    with open('voice_id.txt', 'w') as f:
                        f.write(f"{voice_id}")
                    
                    print(f"Voice ID: {voice_id}")
                    return True
                else:
                    print("No voice_id in first voice")
            else:
                print("No voices found")
        else:
            print(f"HTTP error: {response.status_code}")
    except Exception as e:
        print(f"Exception: {e}")
    
    return False

def main():
    """Main function"""
    
    print("Getting voice ID from known structure...")
    
    success = get_voice_id_from_known_structure()
    
    if success:
        print("SUCCESS: Got voice ID!")
        print("File created: voice_id.txt")
    else:
        print("ERROR: Could not get voice ID")

if __name__ == "__main__":
    main()
