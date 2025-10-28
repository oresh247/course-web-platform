"""
Тест исправленного HeyGen сервиса с правильными API версиями
"""

import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_corrected_heygen_service():
    """Тестирует исправленный HeyGen сервис"""
    
    print("Testing corrected HeyGen service...")
    print("=" * 50)
    
    try:
        from services.heygen_service import HeyGenService
        
        # Инициализируем сервис
        heygen_service = HeyGenService()
        print("SUCCESS: HeyGen service initialized")
        
        # Тест получения аватаров (V2 API)
        print("\n1. Testing avatars (V2 API):")
        try:
            avatars = heygen_service.get_available_avatars()
            print(f"SUCCESS: Got avatars data")
            print(f"Avatars count: {len(avatars.get('data', [])) if isinstance(avatars, dict) else 'Unknown'}")
        except Exception as e:
            print(f"ERROR: {e}")
        
        # Тест получения голосов (V1 API)
        print("\n2. Testing voices (V1 API):")
        try:
            voices = heygen_service.get_available_voices()
            print(f"SUCCESS: Got voices data")
            print(f"Voices count: {len(voices.get('data', [])) if isinstance(voices, dict) else 'Unknown'}")
        except Exception as e:
            print(f"ERROR: {e}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Main function"""
    
    print("CORRECTED HEYGEN SERVICE TEST")
    print("=" * 50)
    
    success = test_corrected_heygen_service()
    
    if success:
        print("\nSUCCESS: Corrected service is working!")
        print("API versions:")
        print("- V2: /v2/video/generate, /v2/avatars")
        print("- V1: /v1/voice.list, /v1/video/{id}, /v1/video/{id}/download")
        
        print("\nNEXT STEPS:")
        print("1. Test video generation with real IDs")
        print("2. Launch the main server")
        print("3. Test API endpoints")
    else:
        print("\nERROR: Service still has issues")

if __name__ == "__main__":
    main()
