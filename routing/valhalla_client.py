from config import VALHALLA_URL, VALHALLA_TIMEOUT
import requests


class ValhallaClient:
    def __init__(
        self,
        base_url: str = VALHALLA_URL,
        timeout: int = VALHALLA_TIMEOUT,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def matrix(self, locations):

        payload = {
            "sources": locations,
            "targets": locations,
            "costing": "auto",
        }

        response = requests.post(
            f"{self.base_url}/sources_to_targets",
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def route(self, locations):

        payload = {
            "locations": locations,
            "costing": "auto",
        }

        response = requests.post(
            f"{self.base_url}/route",
            json=payload,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()
