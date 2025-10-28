"""
Тест генерации видео через HeyGen API
"""

import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_video_generation():
    """Тестирует генерацию видео"""
    
    print("Testing video generation...")
    print("=" * 50)
    
    try:
        from services.heygen_service import HeyGenService
        
        # Инициализируем сервис
        heygen_service = HeyGenService()
        print("SUCCESS: HeyGen service initialized")
        
        # Читаем реальные ID
        try:
            with open('avatar_id.txt', 'r') as f:
                avatar_id = f.read().strip()
            print(f"Avatar ID: {avatar_id}")
        except:
            print("ERROR: Could not read avatar_id.txt")
            return False
        
        try:
            with open('voice_id.txt', 'r') as f:
                voice_id = f.read().strip()
            print(f"Voice ID: {voice_id}")
        except:
            print("ERROR: Could not read voice_id.txt")
            return False
        
        # Тест создания видео
        print("\nCreating test video...")
        try:
            result = heygen_service.create_video_from_text(
                text="Hello! This is a test video from AI Course Builder. We are testing the HeyGen integration.",
                avatar_id=avatar_id,
                voice_id=voice_id
            )
            
            print(f"SUCCESS: Video created!")
            print(f"Result: {result}")
            
            # Проверяем, есть ли video_id
            video_id = result.get('data', {}).get('video_id')
            if video_id:
                print(f"Video ID: {video_id}")
                
                # Проверяем статус видео
                print("\nChecking video status...")
                status_result = heygen_service.get_video_status(video_id)
                print(f"Video status: {status_result}")
                
                return True
            else:
                print("WARNING: No video_id in response")
                print(f"Full result: {result}")
                return False
            
        except Exception as e:
            print(f"ERROR: {e}")
            return False
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Main function"""
    
    print("VIDEO GENERATION TEST")
    print("=" * 50)
    
    success = test_video_generation()
    
    if success:
        print("\nSUCCESS: Video generation is working!")
        print("The HeyGen integration is ready!")
    else:
        print("\nERROR: Video generation failed")

if __name__ == "__main__":
    main()
