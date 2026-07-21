# services/test_weather.py
import os
import sys
from pprint import pprint

# Ensure python can locate the parent modules if run directly from a nested folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.weather_service import WeatherService


def test_weather_pipeline():
    print("==================================================")
    print("[*] Initializing Data.gov.sg Weather Service...")
    print("==================================================\n")

    # 1. Instantiate the service layer (No API keys required for public data.gov.sg)
    weather_svc = WeatherService(collection_id=1459)

    # 2. Fire the query to inspect the metadata response schema
    raw_metadata = weather_svc.fetch_metadata()

    if raw_metadata:
        print("[+] SUCCESS! Received response payload from the API server.\n")
        print("--- Complete Raw Response Dictionary Structure ---")
        pprint(raw_metadata)
    else:
        print("[-] Test Failed. Unable to fetch data from the server endpoint.")


if __name__ == "__main__":
    test_weather_pipeline()
