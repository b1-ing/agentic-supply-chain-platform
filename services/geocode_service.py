"""
Geocoding service for converting addresses into WGS84 coordinates.

Currently uses the Singapore OneMap Search API.

Returned coordinates are (latitude, longitude).
"""

from typing import Optional
import requests


class GeocodingService:
    BASE_URL = "https://www.onemap.gov.sg/api/common/elastic/search"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def geocode(self, address: str) -> Optional[tuple[float, float]]:
        """
        Geocode an address.

        Args:
            address: Free-text address or landmark.

        Returns:
            (latitude, longitude) if found, else None.
        """

        params = {
            "searchVal": address,
            "returnGeom": "Y",
            "getAddrDetails": "Y",
            "pageNum": 1,
        }

        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()

            if int(data.get("found", 0)) == 0:
                return None

            result = data["results"][0]

            lat = float(result["LATITUDE"])
            lon = float(result["LONGITUDE"])

            return lat, lon

        except Exception as e:
            print(f"[Geocoder] Failed to geocode '{address}': {e}")
            return None
