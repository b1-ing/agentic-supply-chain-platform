# services/weather_service.py
import requests
from typing import Dict, Any, Optional

class WeatherService:
    def __init__(self, collection_id: int = 1459):
        """
        Initializes the weather service.
        Collection ID 1459 targets the data.gov.sg v2 weather metadata/dataset.
        """
        self.collection_id = collection_id
        self.base_url = f"https://api-production.data.gov.sg/v2/public/api/collections/{self.collection_id}"

    def fetch_metadata(self) -> Dict[str, Any]:
        """
        Retrieves the structural schema and metadata for the weather collection.
        Useful for validating available fields, coverage zones, and checking api status.
        """
        url = f"{self.base_url}/metadata"

        try:
            print(f"[*] Querying data.gov.sg weather metadata from: {url}")
            response = requests.get(url, timeout=15)

            # Raise an HTTPError if the response code was an error (e.g. 4xx, 5xx)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            # Log the error gracefully to avoid breaking the main pipeline thread
            print(f"[-] Weather API Metadata Fetch Failed: {e}")
            return {}

    def fetch_live_snapshot(self) -> Dict[str, Any]:
        """
        Boilerplate for retrieving the actual live weather values (real-time data).
        Note: Depending on data.gov.sg v2 specifications, real-time records are
        typically pulled from the /snapshot or /data endpoints relative to the collection.
        """
        # If the API documentation specifies an exact endpoint for live data rows:
        url = f"{self.base_url}/snapshot" # or /data depending on the final guide

        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"[!] Target snapshot endpoint returned status code: {response.status_code}")
                return {}
        except Exception as e:
            print(f"[-] Weather API Live Snapshot Failed: {e}")
            return {}