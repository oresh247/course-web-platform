"""
Тест исправленного endpoint для статуса видео
"""

import sys
from pathlib import Path
import requests
import os
from dotenv import load_dotenv

# Добавляем путь к проекту
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Bypass SSL verification for corporate networks
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

load_dotenv()

def test_correct_video_status():
    """Тестирует правильный endpoint для статуса видео"""
    
    print("Testing correct video status endpoint...")
    print("=" * 50)
    
    # Используем последний созданный video_id
    video_id = "957ad844a98f4e5c915d43d77b4a9cd7"
    
    HEYGEN_API_KEY = os.getenv('HEYGEN_API_KEY')
    HEYGEN_BASE_URL = os.getenv('HEYGEN_API_URL', 'https://api.heygen.com')
    
    headers = {
        'X-Api-Key': HEYGEN_API_KEY,
        'Content-Type': 'application/json'
    }
    
    # Тестируем правильный endpoint
    endpoint = f"/v1/video_status.get?video_id={video_id}"
    
    try:
        print(f"Testing: {endpoint}")
        response = requests.get(
            f"{HEYGEN_BASE_URL}{endpoint}",
            headers=headers,
            timeout=10,
            verify=False
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: {result}")
            
            # Проверяем статус видео
            if 'data' in result:
                video_data = result['data']
                status = video_data.get('status', 'unknown')
                print(f"Video status: {status}")
                
                if status == 'completed':
                    video_url = video_data.get('video_url')
                    if video_url:
                        print(f"Video URL: {video_url}")
                        print("Video is ready for download!")
                    else:
                        print("Video completed but no URL found")
                elif status == 'processing':
                    print("Video is still processing...")
                else:
                    print(f"Video status: {status}")
            
            return True
        else:
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_video_list():
    """Тестирует endpoint для списка видео"""
    
    print("\nTesting video list endpoint...")
    print("=" * 50)
    
    HEYGEN_API_KEY = os.getenv('HEYGEN_API_KEY')
    HEYGEN_BASE_URL = os.getenv('HEYGEN_API_URL', 'https://api.heygen.com')
    
    headers = {
        'X-Api-Key': HEYGEN_API_KEY,
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            f"{HEYGEN_BASE_URL}/v1/video.list",
            headers=headers,
            timeout=10,
            verify=False
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"SUCCESS: Got video list")
            print(f"Videos count: {len(result.get('data', {}).get('list', []))}")
            return True
        else:
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Main function"""
    
    print("CORRECT VIDEO STATUS ENDPOINT TEST")
    print("=" * 50)
    
    # Тест статуса видео
    status_success = test_correct_video_status()
    
    # Тест списка видео
    list_success = test_video_list()
    
    if status_success:
        print("\nSUCCESS: Video status endpoint is working!")
        print("The correct endpoint is: /v1/video_status.get?video_id=VIDEO_ID")
    else:
        print("\nWARNING: Video status endpoint still has issues")
    
    if list_success:
        print("SUCCESS: Video list endpoint is working!")
    else:
        print("WARNING: Video list endpoint has issues")

if __name__ == "__main__":
    main()
