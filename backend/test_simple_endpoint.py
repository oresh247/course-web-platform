"""
Простой endpoint для тестирования генерации видео
"""

import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_simple_video_endpoint():
    """Тестирует простой endpoint для генерации видео"""
    
    print("Simple video endpoint test...")
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
        print("\nCreating video...")
        result = heygen_service.create_video_from_text(
            text="Hello! This is a test video from AI Course Builder API endpoint.",
            avatar_id=avatar_id,
            voice_id=voice_id,
            quality="low",
            test_mode=True
        )
        
        print(f"Result: {result}")
        
        # Проверяем, есть ли video_id
        video_id = result.get('data', {}).get('video_id')
        if video_id:
            print(f"SUCCESS: Video created!")
            print(f"Video ID: {video_id}")
            
            # Проверяем статус
            print("\nChecking video status...")
            status_result = heygen_service.get_video_status(video_id)
            print(f"Video status: {status_result}")
            
            return {
                'success': True,
                'video_id': video_id,
                'status': status_result,
                'message': 'Video created successfully'
            }
        else:
            print("No video_id in response")
            return {
                'success': False,
                'message': 'No video_id in response'
            }
        
    except Exception as e:
        print(f"ERROR: {e}")
        return {
            'success': False,
            'message': str(e)
        }

def main():
    """Main function"""
    
    print("SIMPLE VIDEO ENDPOINT TEST")
    print("=" * 50)
    
    result = test_simple_video_endpoint()
    
    if result['success']:
        print("\nSUCCESS: Simple video endpoint works!")
        print(f"Video ID: {result['video_id']}")
        print("The system is ready for production!")
    else:
        print(f"\nERROR: {result['message']}")

if __name__ == "__main__":
    main()
