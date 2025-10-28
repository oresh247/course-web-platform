"""
Тест работы системы с мок HeyGen сервисом
"""

import sys
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_mock_heygen():
    """Тестирует работу с мок HeyGen сервисом"""
    
    print("🧪 Тестирование мок HeyGen сервиса")
    print("=" * 50)
    
    try:
        from services.mock_heygen_service import MockHeyGenService, AdaptiveHeyGenService
        
        print("✅ Мок сервисы импортированы успешно")
        
        # Тест мок сервиса
        print("\n1️⃣ Тест MockHeyGenService:")
        mock_service = MockHeyGenService()
        
        # Тест получения аватаров
        avatars = mock_service.get_available_avatars()
        print(f"✅ Аватары получены: {len(avatars['data'])} шт.")
        
        # Тест получения голосов
        voices = mock_service.get_available_voices()
        print(f"✅ Голоса получены: {len(voices['data'])} шт.")
        
        # Тест создания видео
        video_result = mock_service.create_lesson_video(
            lesson_title="Тестовый урок",
            lesson_content="Это тестовый контент для мок-видео."
        )
        print(f"✅ Видео создано: {video_result['video_id']}")
        
        # Тест адаптивного сервиса
        print("\n2️⃣ Тест AdaptiveHeyGenService:")
        adaptive_service = AdaptiveHeyGenService()
        
        avatars_adaptive = adaptive_service.get_available_avatars()
        print(f"✅ Адаптивный сервис работает: {len(avatars_adaptive['data'])} аватаров")
        
        print("\n🎉 Все тесты мок-сервиса пройдены!")
        print("✅ Система может работать без реального HeyGen API")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании мок-сервиса: {e}")
        return False

def test_video_generation_service():
    """Тестирует VideoGenerationService с мок сервисом"""
    
    print("\n3️⃣ Тест VideoGenerationService:")
    
    try:
        from services.video_generation_service import VideoGenerationService
        
        video_service = VideoGenerationService()
        print("✅ VideoGenerationService инициализирован")
        
        # Тест получения аватаров через сервис
        avatars = video_service.heygen_service.get_available_avatars()
        print(f"✅ Аватары через сервис: {len(avatars['data'])} шт.")
        
        print("✅ VideoGenerationService работает с мок-сервисом")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка VideoGenerationService: {e}")
        return False

def test_fastapi_integration():
    """Тестирует интеграцию с FastAPI"""
    
    print("\n4️⃣ Тест FastAPI интеграции:")
    
    try:
        from fastapi import FastAPI
        from routes.video_routes import router as video_router
        
        app = FastAPI(title="AI Course Builder - Mock Test")
        app.include_router(video_router)
        
        print("✅ FastAPI приложение с видео роутами создано")
        print("✅ Можете запустить сервер: uvicorn main:app --reload")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка FastAPI интеграции: {e}")
        return False

def main():
    """Основная функция тестирования"""
    
    print("🚀 Тестирование системы с мок HeyGen сервисом")
    print("=" * 60)
    
    # Тест 1: Мок сервис
    mock_ok = test_mock_heygen()
    
    if not mock_ok:
        print("❌ Мок сервис не работает")
        return
    
    # Тест 2: VideoGenerationService
    service_ok = test_video_generation_service()
    
    # Тест 3: FastAPI интеграция
    api_ok = test_fastapi_integration()
    
    print("\n" + "=" * 60)
    print("📋 Результаты тестирования:")
    print(f"✅ Мок HeyGen сервис: {'Работает' if mock_ok else 'Ошибка'}")
    print(f"✅ VideoGenerationService: {'Работает' if service_ok else 'Ошибка'}")
    print(f"✅ FastAPI интеграция: {'Работает' if api_ok else 'Ошибка'}")
    
    if mock_ok and service_ok and api_ok:
        print("\n🎉 Система готова к работе!")
        print("🎬 Видео-функции будут работать в мок-режиме")
        print("🚀 Запустите сервер: uvicorn main:app --reload")
        print("📚 Документация: http://localhost:8000/api/docs")
    else:
        print("\n⚠️ Есть проблемы с интеграцией")

if __name__ == "__main__":
    main()
