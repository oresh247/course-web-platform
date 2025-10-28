"""
Простой тест генерации видео через API
"""

import requests
import json

def test_simple_video_generation():
    """Тестирует простую генерацию видео"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("Simple video generation test...")
    print("=" * 50)
    
    # Простой payload для генерации видео
    payload = {
        "title": "Test Lesson",
        "text": "Hello! This is a test video from AI Course Builder API.",
        "avatar_id": "Abigail_expressive_2024112501",
        "voice_id": "9799f1ba6acd4b2b993fe813a18f9a91",
        "quality": "low",
        "test_mode": True
    }
    
    try:
        print("Sending request to generate video...")
        response = requests.post(f"{base_url}/api/video/generate-lesson", json=payload)
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: {data}")
            
            if 'data' in data and 'video' in data['data']:
                video_info = data['data']['video']
                video_id = video_info.get('video_id')
                if video_id:
                    print(f"Video ID: {video_id}")
                    
                    # Check video status
                    print(f"\nChecking video status...")
                    status_response = requests.get(f"{base_url}/api/video/status/{video_id}")
                    print(f"Status: {status_response.status_code}")
                    print(f"Status data: {status_response.json()}")
                    
                    return True
            
        else:
            print(f"ERROR: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Main function"""
    
    print("SIMPLE VIDEO GENERATION TEST")
    print("=" * 50)
    
    success = test_simple_video_generation()
    
    if success:
        print("\nSUCCESS: Video generation through API works!")
    else:
        print("\nERROR: Video generation through API failed")

if __name__ == "__main__":
    main()
