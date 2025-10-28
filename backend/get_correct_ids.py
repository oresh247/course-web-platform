"""
Исправленное извлечение ID с правильной обработкой структуры данных
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_correct_ids():
    """Правильное получение ID"""
    
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
            
            # Проверяем структуру
            if 'data' in data:
                avatars_data = data['data']
                
                # Если data содержит список аватаров
                if isinstance(avatars_data, list) and avatars_data:
                    first_avatar = avatars_data[0]
                    if isinstance(first_avatar, dict):
                        avatar_id = first_avatar.get('avatar_id', 'N/A')
                        
                        # Сохраняем
                        with open('avatar_id.txt', 'w') as f:
                            f.write(f"{avatar_id}")
                        
                        print(f"Avatar ID: {avatar_id}")
                        return True
                
                # Если data содержит информацию об аватарах в другом формате
                elif isinstance(avatars_data, dict):
                    # Ищем аватары в разных возможных ключах
                    for key in ['avatars', 'items', 'list']:
                        if key in avatars_data and isinstance(avatars_data[key], list):
                            avatars = avatars_data[key]
                            if avatars:
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
    
    print("Getting correct IDs...")
    
    success = get_correct_ids()
    
    if success:
        print("SUCCESS: Got IDs!")
        print("Files created: avatar_id.txt, voice_id.txt")
    else:
        print("ERROR: Could not get IDs")

if __name__ == "__main__":
    main()
