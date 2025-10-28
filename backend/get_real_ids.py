"""
Получение реальных ID аватаров для тестирования
"""

import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def get_real_avatar_ids():
    """Получает реальные ID аватаров"""
    
    print("Getting real avatar IDs...")
    print("=" * 40)
    
    try:
        from services.heygen_service import HeyGenService
        
        # Инициализируем сервис
        heygen_service = HeyGenService()
        
        # Получаем аватары
        avatars_data = heygen_service.get_available_avatars()
        
        if avatars_data and 'data' in avatars_data:
            avatars = avatars_data['data']
            print(f"Found {len(avatars)} avatars")
            
            print("\nFirst 5 avatars:")
            for i, avatar in enumerate(avatars[:5], 1):
                avatar_id = avatar.get('avatar_id', 'N/A')
                avatar_name = avatar.get('name', 'No name')
                print(f"  {i}. ID: {avatar_id}")
                print(f"     Name: {avatar_name}")
                print()
            
            # Возвращаем первый доступный аватар
            if avatars:
                first_avatar = avatars[0]
                avatar_id = first_avatar.get('avatar_id')
                avatar_name = first_avatar.get('name', 'Unknown')
                
                print(f"RECOMMENDED AVATAR:")
                print(f"  ID: {avatar_id}")
                print(f"  Name: {avatar_name}")
                
                return avatar_id, avatar_name
        
        return None, None
        
    except Exception as e:
        print(f"ERROR: {e}")
        return None, None

def get_real_voice_ids():
    """Получает реальные ID голосов"""
    
    print("\nGetting real voice IDs...")
    print("=" * 40)
    
    try:
        from services.heygen_service import HeyGenService
        
        # Инициализируем сервис
        heygen_service = HeyGenService()
        
        # Получаем голоса
        voices_data = heygen_service.get_available_voices()
        
        if voices_data and 'data' in voices_data:
            voices = voices_data['data']
            print(f"Found {len(voices)} voices")
            
            # Ищем английские голоса
            english_voices = [v for v in voices if v.get('language', '').lower() in ['english', 'en', 'multilingual']]
            
            print(f"\nFound {len(english_voices)} English/Multilingual voices")
            
            print("\nFirst 3 English voices:")
            for i, voice in enumerate(english_voices[:3], 1):
                voice_id = voice.get('voice_id', 'N/A')
                voice_lang = voice.get('language', 'Unknown')
                voice_gender = voice.get('gender', 'Unknown')
                print(f"  {i}. ID: {voice_id}")
                print(f"     Language: {voice_lang}")
                print(f"     Gender: {voice_gender}")
                print()
            
            # Возвращаем первый английский голос
            if english_voices:
                first_voice = english_voices[0]
                voice_id = first_voice.get('voice_id')
                voice_lang = first_voice.get('language', 'Unknown')
                
                print(f"RECOMMENDED VOICE:")
                print(f"  ID: {voice_id}")
                print(f"  Language: {voice_lang}")
                
                return voice_id, voice_lang
        
        return None, None
        
    except Exception as e:
        print(f"ERROR: {e}")
        return None, None

def main():
    """Main function"""
    
    print("GETTING REAL AVATAR AND VOICE IDs")
    print("=" * 50)
    
    # Получаем ID аватаров
    avatar_id, avatar_name = get_real_avatar_ids()
    
    # Получаем ID голосов
    voice_id, voice_lang = get_real_voice_ids()
    
    # Результаты
    print("\n" + "=" * 50)
    print("SUMMARY:")
    
    if avatar_id and voice_id:
        print("SUCCESS: Got real IDs!")
        print(f"Avatar ID: {avatar_id}")
        print(f"Voice ID: {voice_id}")
        
        print("\nNEXT STEPS:")
        print("1. Test video generation with these IDs")
        print("2. Update environment variables")
        print("3. Launch the server")
        
        # Сохраняем в файл для использования
        with open('real_ids.txt', 'w') as f:
            f.write(f"AVATAR_ID={avatar_id}\n")
            f.write(f"VOICE_ID={voice_id}\n")
            f.write(f"AVATAR_NAME={avatar_name}\n")
            f.write(f"VOICE_LANG={voice_lang}\n")
        
        print(f"\nSaved to real_ids.txt")
        
    else:
        print("ERROR: Could not get real IDs")

if __name__ == "__main__":
    main()
