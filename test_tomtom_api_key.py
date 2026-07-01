# test_tomtom_key.py
import os
from dotenv import load_dotenv
import requests

# 1. Load configuration from the local .env file
load_dotenv()

def test_tomtom_api_key():
    # 2. Extract the string value from the environment variable manager
    api_key = os.getenv("TOMTOM_API_KEY")

    if not api_key:
        print("[-] ERROR: TOMTOM_API_KEY not found in environment variables or .env file.")
        return

    lat, lon = 1.3521, 103.8198
    zoom_level = 18
    url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/{zoom_level}/json"
    params = {"key": api_key, "point": f"{lat},{lon}"}

    print(f"[*] Dispatching test ping using key: {api_key[:5]}...{api_key[-5:] if len(api_key) > 5 else ''}")

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            print("[+] SUCCESS: Your environment variable TomTom API key works!")
        else:
            print(f"[-] ERROR {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[-] Connection Error: {e}")

if __name__ == "__main__":
    test_tomtom_api_key()