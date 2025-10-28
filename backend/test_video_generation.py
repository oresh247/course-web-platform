"""
Тест создания видео с реальными ID
"""

import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_video_generation():
    """Тестирует создание видео с реальными ID"""
    
    print("Testing video generation with real IDs...")
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
        print("\n3. Testing video generation:")
        try:
            result = heygen_service.create_video_from_text(
                text="Hello! This is a test video from AI Course Builder.",
                avatar_id=avatar_id,
                voice_id=voice_id
            )
            
            print(f"SUCCESS: Video created!")
            print(f"Video ID: {result.get('video_id', 'N/A')}")
            print(f"Status: {result.get('status', 'N/A')}")
            
            return True
            
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
        print("The system is ready for production!")
        
        print("\nNEXT STEPS:")
        print("1. Launch the main server")
        print("2. Test API endpoints")
        print("3. Integrate with frontend")
    else:
        print("\nERROR: Video generation failed")

if __name__ == "__main__":
    main()
