"""
Тест различных endpoints для проверки статуса видео
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

def test_video_status_endpoints():
    """Тестирует различные endpoints для проверки статуса видео"""
    
    print("Testing video status endpoints...")
    print("=" * 50)
    
    # Используем последний созданный video_id
    video_id = "e26643c48df0479bb1888f9986cc9f9f"
    
    HEYGEN_API_KEY = os.getenv('HEYGEN_API_KEY')
    HEYGEN_BASE_URL = os.getenv('HEYGEN_API_URL', 'https://api.heygen.com')
    
    headers = {
        'X-Api-Key': HEYGEN_API_KEY,
        'Content-Type': 'application/json'
    }
    
    # Тестируем различные endpoints
    endpoints = [
        f"/v1/video/{video_id}",
        f"/v1/video.get?video_id={video_id}",
        f"/v2/video/{video_id}",
        f"/v2/video/{video_id}/status",
        f"/v1/video/{video_id}/status",
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\nTesting: {endpoint}")
            response = requests.get(
                f"{HEYGEN_BASE_URL}{endpoint}",
                headers=headers,
                timeout=10,
                verify=False
            )
            
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"SUCCESS: {response.json()}")
                return endpoint
            else:
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"ERROR: {e}")
    
    return None

def main():
    """Main function"""
    
    print("VIDEO STATUS ENDPOINTS TEST")
    print("=" * 50)
    
    working_endpoint = test_video_status_endpoints()
    
    if working_endpoint:
        print(f"\nSUCCESS: Found working endpoint: {working_endpoint}")
    else:
        print("\nWARNING: No working status endpoint found")
        print("Video generation works, but status checking needs investigation")

if __name__ == "__main__":
    main()
