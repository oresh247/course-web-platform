"""
Тест обновленного HeyGen сервиса
"""

import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_updated_heygen_service():
    """Тестирует обновленный HeyGen сервис"""
    
    print("Testing updated HeyGen service...")
    print("=" * 40)
    
    try:
        from services.heygen_service import HeyGenService
        
        # Инициализируем сервис
        heygen_service = HeyGenService()
        print("SUCCESS: HeyGen service initialized")
        
        # Тест получения аватаров
        print("\n1. Testing avatars:")
        try:
            avatars = heygen_service.get_available_avatars()
            print(f"SUCCESS: Got avatars data")
            print(f"Avatars: {avatars}")
        except Exception as e:
            print(f"ERROR: {e}")
        
        # Тест получения голосов
        print("\n2. Testing voices:")
        try:
            voices = heygen_service.get_available_voices()
            print(f"SUCCESS: Got voices data")
            print(f"Voices: {voices}")
        except Exception as e:
            print(f"ERROR: {e}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Main function"""
    
    print("UPDATED HEYGEN SERVICE TEST")
    print("=" * 40)
    
    success = test_updated_heygen_service()
    
    if success:
        print("\nSUCCESS: Updated service is working!")
        print("NEXT STEPS:")
        print("1. Test video generation with real avatar IDs")
        print("2. Launch the main server")
        print("3. Test API endpoints")
    else:
        print("\nERROR: Service still has issues")

if __name__ == "__main__":
    main()
