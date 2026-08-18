# services/lta_service.py

import os
import time
from typing import List, Dict, Any, Tuple
import requests
import networkx as nx
from shapely.geometry import LineString
from shapely.strtree import STRtree
from dotenv import load_dotenv
import httpx
import asyncio
import math
import geopandas as gpd
import json
from six import print_

load_dotenv()


class LTADataMallClient:
    """
    The key entrypoint to accessing the LTA traffic data from the DataMall.

    Make sure that you get a API key from LTA!

    """
    def __init__(self, account_key: str = None):
        self.account_key = account_key or os.getenv("LTA_ACCOUNT_KEY")
        if not self.account_key:
            raise ValueError(
                "LTA AccountKey must be provided or set in environment variables."
            )

        self.base_url = "https://datamall2.mytransport.sg/ltaodataservice"
        self.headers = {"AccountKey": self.account_key, "accept": "application/json"}



    def fetch_all_pages(self, endpoint: str) -> List[Dict[str, Any]]:
        """
        Fetches all relevant results from the specified endpoint.

        Handles the 500-record pagination limit automatically via OData ?$skip

        For more info on the endpoints, see: https://datamall.lta.gov.sg/content/dam/datamall/datasets/LTA_DataMall_API_User_Guide.pdf?ref=public_apis&utm_medium=website
        """
        results = []
        skip = 0
        page = 1
        url = f"{self.base_url}/{endpoint}"
        print(url)

        while skip < 1000:  # REVERT TO TRUE AFTER TESTING
            params = {"$skip": skip} if skip > 0 else {}
            try:
                response = requests.get(
                    url, headers=self.headers, params=params, timeout=15
                )
                if response.status_code != 200:
                    print(
                        f"[-] LTA API Error {response.status_code} on {endpoint}: {response.text}"
                    )
                    break

                data = response.json()
                records = data.get("value", [])

                print(f"[*] Page {page}: fetched {len(records)} records (skip={skip})")

                if not records:
                    print("[*] No more records.")
                    break

                results.extend(records)

                if len(records) < 500:
                    print("[+] Last page reached.")
                    break

                skip += 500
#                 time.sleep(0.1)  # Small throttle to respect rate limits
            except Exception as e:
                print(f"[-] Request failed on endpoint {endpoint}: {e}")
                break

        return results