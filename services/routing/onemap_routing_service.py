# services/routing/onemap_routing_service.py

from __future__ import annotations

import requests
import os
from dotenv import load_dotenv

load_dotenv()


from websockets import headers


class OneMapRoutingService:

    def __init__(
            self,
            base_url: str = "https://www.onemap.gov.sg",
    ):
        self.base_url = base_url.rstrip("/")
        self.token = os.getenv("ONEMAP_API_KEY")

    @property
    def headers(self):

        return {
            "Authorization": self.token,
        }

    ####################################################################
    # Route
    ####################################################################

    def route(
            self,
            start_lat: float,
            start_lon: float,
            end_lat: float,
            end_lon: float,
    ):
        print("token:", os.getenv("ONEMAP_API_KEY"))

        response = requests.get(
            f"{self.base_url}/api/public/routingsvc/route",
            params={
                "start": f"{start_lat},{start_lon}",
                "end": f"{end_lat},{end_lon}",
                "routeType": "drive",
            },
            headers=self.headers,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()