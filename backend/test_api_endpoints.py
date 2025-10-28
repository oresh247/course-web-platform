"""
Тест API endpoints сервера
"""

import requests
import json

def test_api_endpoints():
    """Тестирует API endpoints сервера"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("Testing API endpoints...")
    print("=" * 50)
    
    # 1. Health check
    print("1. Health check:")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 2. Video avatars
    print("\n2. Video avatars:")
    try:
        response = requests.get(f"{base_url}/api/video/avatars")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Avatars count: {len(data.get('data', []))}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 3. Video voices
    print("\n3. Video voices:")
    try:
        response = requests.get(f"{base_url}/api/video/voices")
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Voices count: {len(data.get('data', []))}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 4. Test video generation
    print("\n4. Test video generation:")
    try:
        payload = {
            "text": "Hello! This is a test video from AI Course Builder API.",
            "avatar_id": "Abigail_expressive_2024112501",
            "voice_id": "9799f1ba6acd4b2b993fe813a18f9a91",
            "quality": "low",
            "test_mode": True
        }
        response = requests.post(f"{base_url}/api/video/generate-lesson", json=payload)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {data}")
        
        if response.status_code == 200 and 'video_id' in data:
            video_id = data['video_id']
            print(f"Video ID: {video_id}")
            
            # Check video status
            print(f"\n5. Video status for {video_id}:")
            status_response = requests.get(f"{base_url}/api/video/status/{video_id}")
            print(f"Status: {status_response.status_code}")
            print(f"Status data: {status_response.json()}")
        
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Main function"""
    
    print("API ENDPOINTS TEST")
    print("=" * 50)
    
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    print("API testing completed!")

if __name__ == "__main__":
    main()
