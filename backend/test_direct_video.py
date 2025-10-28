"""
Простой тест генерации видео напрямую через HeyGen сервис
"""

import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_direct_video_generation():
    """Тестирует генерацию видео напрямую через HeyGen сервис"""
    
    print("Direct video generation test...")
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
        
        # Тест создания видео
        print("\nCreating video directly...")
        result = heygen_service.create_video_from_text(
            text="Hello! This is a direct test video from AI Course Builder.",
            avatar_id=avatar_id,
            voice_id=voice_id,
            quality="low",
            test_mode=True
        )
        
        print(f"Result: {result}")
        
        # Проверяем, есть ли video_id
        video_id = result.get('data', {}).get('video_id')
        if video_id:
            print(f"SUCCESS: Video created directly!")
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
    
    print("DIRECT VIDEO GENERATION TEST")
    print("=" * 50)
    
    success = test_direct_video_generation()
    
    if success:
        print("\nSUCCESS: Direct video generation works!")
        print("The HeyGen service is working perfectly!")
    else:
        print("\nERROR: Direct video generation failed")

if __name__ == "__main__":
    main()
