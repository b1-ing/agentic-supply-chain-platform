# services/lta_base_client.py
import requests
import time
from typing import Dict, Any, List
from dotenv import load_dotenv
load_dotenv()  # This automatically finds the .env file and injects the variables

class LTADataMallClient:
    def __init__(self, account_key: str = None):
        # Fallback to environment variable if not passed explicitly
        import os
        self.account_key = account_key or os.getenv("LTA_ACCOUNT_KEY")
        if not self.account_key:
            raise ValueError("LTA AccountKey must be provided or set in environment variables.")

        self.base_url = "http://datamall2.mytransport.sg/ltaodataservice"
        self.headers = {
            "AccountKey": self.account_key,
            "accept": "application/json"
        }

    def fetch_all_pages(self, endpoint: str) -> List[Dict[str, Any]]:
        """
        Handles the 500-record pagination limit automatically via OData ?$skip
        """
        results = []
        skip = 0
        url = f"{self.base_url}/{endpoint}"

        while True:
            params = {"$skip": skip} if skip > 0 else {}
            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code != 200:
                # In production, log this gracefully to avoid crashing the pipeline
                raise RuntimeError(f"LTA API Error {response.status_code}: {response.text}")

            data = response.json()
            # LTA payloads wrap arrays inside a 'value' key
            records = data.get("value", [])

            if not records:
                break

            results.extend(records)

            if len(records) < 500:
                break # We fetched the last page

            skip += 500
            time.sleep(0.1) # Small throttle to respect rate limits

        return results