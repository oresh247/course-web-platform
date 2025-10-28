"""
Тест создания видео с низким разрешением
"""

import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_low_resolution_video():
    """Тестирует создание видео с низким разрешением"""
    
    print("Testing low resolution video creation...")
    print("=" * 50)
    
    try:
        from services.heygen_service import HeyGenService
        
        # Инициализируем сервис
        heygen_service = HeyGenService()
        print("SUCCESS: HeyGen service initialized")
        
        # Читаем реальные ID
        with open('avatar_id.txt', 'r') as f:
            avatar_id = f.read().strip()
        print(f"Avatar ID: {avatar_id}")
        
        with open('voice_id.txt', 'r') as f:
            voice_id = f.read().strip()
        print(f"Voice ID: {voice_id}")
        
        # Тест создания видео с низким разрешением
        print("\nCreating low resolution video...")
        
        # Модифицируем payload для низкого разрешения
        import requests
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        HEYGEN_API_KEY = os.getenv('HEYGEN_API_KEY')
        HEYGEN_BASE_URL = os.getenv('HEYGEN_API_URL', 'https://api.heygen.com')
        
        headers = {
            'X-Api-Key': HEYGEN_API_KEY,
            'Content-Type': 'application/json'
        }
        
        # Payload с низким разрешением
        payload = {
            "background": {
                "type": "color",
                "value": "#ffffff"
            },
            "clips": [
                {
                    "avatar_id": avatar_id,
                    "voice_id": voice_id,
                    "script": {
                        "type": "text",
                        "input": "Hello! This is a low resolution test video."
                    }
                }
            ],
            "ratio": "16:9",
            "test": True,  # Тестовый режим
            "version": "v2",
            "quality": "low"  # Низкое качество
        }
        
        try:
            response = requests.post(
                f"{HEYGEN_BASE_URL}/v2/video/generate",
                headers=headers,
                json=payload,
                timeout=30,
                verify=False
            )
            
            print(f"Response status: {response.status_code}")
            result = response.json()
            print(f"Result: {result}")
            
            if response.status_code == 200:
                video_id = result.get('data', {}).get('video_id')
                if video_id:
                    print(f"SUCCESS: Low resolution video created!")
                    print(f"Video ID: {video_id}")
                    
                    # Проверяем статус
                    print("\nChecking video status...")
                    status_result = heygen_service.get_video_status(video_id)
                    print(f"Video status: {status_result}")
                    
                    return True
                else:
                    print("No video_id in response")
                    return False
            else:
                print(f"Error: {result}")
                return False
                
        except Exception as e:
            print(f"ERROR: {e}")
            return False
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Main function"""
    
    print("LOW RESOLUTION VIDEO TEST")
    print("=" * 50)
    
    success = test_low_resolution_video()
    
    if success:
        print("\nSUCCESS: Low resolution video creation works!")
    else:
        print("\nERROR: Low resolution video creation failed")

if __name__ == "__main__":
    main()
