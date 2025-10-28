"""
Тест генерации видео на каждый слайд урока
"""

import requests
import json

def test_slide_video_generation():
    """Тестирует генерацию видео на каждый слайд"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("Testing slide video generation...")
    print("=" * 50)
    
    # Payload для урока с несколькими слайдами
    lesson_data = {
        "title": "Основы Python программирования",
        "description": "Введение в Python для начинающих",
        "text": """Добро пожаловать в мир Python!

Python - это мощный и простой язык программирования.

В этом уроке мы изучим основы синтаксиса Python.

Мы также рассмотрим переменные и типы данных.

В конце урока вы сможете написать свою первую программу.""",
        "avatar_id": "Abigail_expressive_2024112501",
        "voice_id": "9799f1ba6acd4b2b993fe813a18f9a91",
        "quality": "low",
        "test_mode": True,
        "language": "ru"
    }
    
    try:
        print("Sending request to generate lesson with slide videos...")
        response = requests.post(f"{base_url}/api/video/generate-lesson-slides", json=lesson_data)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: {data.get('message')}")
            
            lesson_result = data.get('data', {})
            print(f"Lesson title: {lesson_result.get('title')}")
            print(f"Total slides: {lesson_result.get('total_slides')}")
            
            slides = lesson_result.get('slides', [])
            print(f"\nGenerated videos for {len(slides)} slides:")
            
            for slide in slides:
                slide_number = slide.get('slide_number')
                slide_title = slide.get('slide_title')
                video_info = slide.get('video', {})
                video_id = video_info.get('video_id')
                status = video_info.get('status')
                
                print(f"  Slide {slide_number}: {slide_title}")
                print(f"    Video ID: {video_id}")
                print(f"    Status: {status}")
                
                if video_id:
                    # Check video status
                    print(f"    Checking status...")
                    status_response = requests.get(f"{base_url}/api/video/status/{video_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        video_status = status_data.get('data', {}).get('status', 'unknown')
                        print(f"    HeyGen Status: {video_status}")
                
                print()
            
            return True
            
        else:
            print(f"ERROR: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_single_slide_lesson():
    """Тестирует генерацию видео для урока с одним слайдом"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("\nTesting single slide lesson...")
    print("=" * 50)
    
    # Payload для урока с одним слайдом
    lesson_data = {
        "title": "Краткий урок",
        "description": "Простой урок с одним слайдом",
        "text": "Это короткий урок с одним слайдом для тестирования.",
        "avatar_id": "Abigail_expressive_2024112501",
        "voice_id": "9799f1ba6acd4b2b993fe813a18f9a91",
        "quality": "low",
        "test_mode": True
    }
    
    try:
        response = requests.post(f"{base_url}/api/video/generate-lesson-slides", json=lesson_data)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: {data.get('message')}")
            
            lesson_result = data.get('data', {})
            print(f"Total slides: {lesson_result.get('total_slides')}")
            
            slides = lesson_result.get('slides', [])
            if slides:
                slide = slides[0]
                video_info = slide.get('video', {})
                video_id = video_info.get('video_id')
                print(f"Single slide video ID: {video_id}")
            
            return True
        else:
            print(f"ERROR: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Main function"""
    
    print("SLIDE VIDEO GENERATION TEST")
    print("=" * 50)
    
    # Тест 1: Урок с несколькими слайдами
    success1 = test_slide_video_generation()
    
    # Тест 2: Урок с одним слайдом
    success2 = test_single_slide_lesson()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("SUCCESS: Slide video generation works perfectly!")
        print("The system can generate videos for each slide of a lesson!")
    else:
        print("ERROR: Some tests failed")

if __name__ == "__main__":
    main()
