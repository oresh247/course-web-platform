"""
Детальная отладка структуры голосов
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def debug_voices():
    """Отладка структуры голосов"""
    
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
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Data type: {type(data)}")
            print(f"Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # Проверяем структуру
            if isinstance(data, dict):
                voices_data = data.get('data', [])
                print(f"Voices data type: {type(voices_data)}")
                print(f"Voices data length: {len(voices_data) if isinstance(voices_data, list) else 'Not a list'}")
                
                if isinstance(voices_data, list) and voices_data:
                    first_voice = voices_data[0]
                    print(f"First voice type: {type(first_voice)}")
                    
                    if isinstance(first_voice, dict):
                        voice_id = first_voice.get('voice_id', 'N/A')
                        voice_lang = first_voice.get('language', 'Unknown')
                        print(f"Voice ID: {voice_id}")
                        print(f"Voice language: {voice_lang}")
                        
                        # Сохраняем
                        with open('voice_id.txt', 'w') as f:
                            f.write(f"{voice_id}")
                        
                        print("SUCCESS: Saved voice ID!")
                        return True
                    else:
                        print(f"First voice is not a dict: {first_voice}")
                else:
                    print(f"Voices data is not a list or empty: {voices_data}")
            else:
                print(f"Data is not a dict: {data}")
        else:
            print(f"ERROR: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    return False

def main():
    """Main function"""
    
    print("Debugging voices structure...")
    
    success = debug_voices()
    
    if success:
        print("SUCCESS: Got voice ID!")
    else:
        print("ERROR: Could not get voice ID")

if __name__ == "__main__":
    main()
