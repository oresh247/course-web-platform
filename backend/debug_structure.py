"""
Детальная отладка структуры данных HeyGen API
"""

import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

def debug_data_structure():
    """Отлаживает структуру данных HeyGen API"""
    
    api_key = os.getenv('HEYGEN_API_KEY')
    if not api_key:
        print("ERROR: HEYGEN_API_KEY not found")
        return False
    
    headers = {
        'X-Api-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    print("Debugging HeyGen API data structure...")
    print("=" * 50)
    
    # Отладка аватаров
    print("\n1. Debugging avatars:")
    try:
        response = requests.get(
            'https://api.heygen.com/v2/avatars',
            headers=headers,
            timeout=10,
            verify=False
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Data type: {type(data)}")
            print(f"   Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            # Проверяем структуру
            if isinstance(data, dict):
                avatars = data.get('data', [])
                print(f"   Avatars type: {type(avatars)}")
                print(f"   Avatars length: {len(avatars) if isinstance(avatars, list) else 'Not a list'}")
                
                if isinstance(avatars, list) and avatars:
                    print(f"   First avatar type: {type(avatars[0])}")
                    print(f"   First avatar: {avatars[0]}")
                    
                    if isinstance(avatars[0], dict):
                        avatar_id = avatars[0].get('avatar_id', 'N/A')
                        avatar_name = avatars[0].get('name', 'No name')
                        print(f"   SUCCESS! Avatar ID: {avatar_id}")
                        print(f"   Avatar name: {avatar_name}")
                        
                        # Сохраняем
                        with open('avatar_id.txt', 'w') as f:
                            f.write(f"{avatar_id}")
                        print(f"   Saved to avatar_id.txt")
                        
                        return True
                    else:
                        print(f"   ERROR: First avatar is not a dict: {avatars[0]}")
                else:
                    print(f"   ERROR: Avatars is not a list or empty: {avatars}")
            else:
                print(f"   ERROR: Data is not a dict: {data}")
        else:
            print(f"   ERROR: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"   EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
    
    return False

def main():
    """Main function"""
    
    print("HEYGEN DATA STRUCTURE DEBUG")
    print("=" * 50)
    
    success = debug_data_structure()
    
    if success:
        print("\nSUCCESS: Got avatar ID!")
    else:
        print("\nERROR: Could not get avatar ID")

if __name__ == "__main__":
    main()
