"""
Простое извлечение ID голоса
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_voice_id_simple():
    """Простое получение ID голоса"""
    
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
            
            # Проверяем структуру
            if 'data' in data:
                voices_data = data['data']
                
                # Если data содержит список голосов
                if isinstance(voices_data, list) and voices_data:
                    first_voice = voices_data[0]
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
    
    print("Getting voice ID...")
    
    success = get_voice_id_simple()
    
    if success:
        print("SUCCESS: Got voice ID!")
        print("File created: voice_id.txt")
    else:
        print("ERROR: Could not get voice ID")

if __name__ == "__main__":
    main()
