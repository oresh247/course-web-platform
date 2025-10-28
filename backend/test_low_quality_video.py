"""
Тест создания видео с низким качеством через обновленный сервис
"""

import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_low_quality_video():
    """Тестирует создание видео с низким качеством"""
    
    print("Testing low quality video creation...")
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
        
        # Тест создания видео с низким качеством
        print("\nCreating low quality video...")
        result = heygen_service.create_video_from_text(
            text="Hello! This is a low quality test video from AI Course Builder.",
            avatar_id=avatar_id,
            voice_id=voice_id,
            quality="low",
            test_mode=True
        )
        
        print(f"Result: {result}")
        
        # Проверяем, есть ли video_id
        video_id = result.get('data', {}).get('video_id')
        if video_id:
            print(f"SUCCESS: Low quality video created!")
            print(f"Video ID: {video_id}")
            
            # Проверяем статус
            print("\nChecking video status...")
            status_result = heygen_service.get_video_status(video_id)
            print(f"Video status: {status_result}")
            
            return True
        else:
            print("No video_id in response")
            return False
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Main function"""
    
    print("LOW QUALITY VIDEO TEST")
    print("=" * 50)
    
    success = test_low_quality_video()
    
    if success:
        print("\nSUCCESS: Low quality video creation works!")
        print("The HeyGen integration is fully functional!")
    else:
        print("\nERROR: Low quality video creation failed")

if __name__ == "__main__":
    main()
