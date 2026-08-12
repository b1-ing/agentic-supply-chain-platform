from __future__ import annotations

import os
import time

import requests


class OneMapAuthService:
    """
    Handles OneMap authentication and automatically refreshes
    the access token when it expires.
    """

    AUTH_URL = "https://www.onemap.gov.sg/api/auth/post/getToken"

    def __init__(self):

        self.email = os.getenv("ONEMAP_EMAIL")
        self.password = os.getenv("ONEMAP_PASSWORD")

        if not self.email or not self.password:
            raise RuntimeError("ONEMAP_EMAIL and ONEMAP_PASSWORD must be set.")

        self._token: str | None = None
        self._expiry: int = 0

    ####################################################################
    # Public API
    ####################################################################

    def access_token(self) -> str:

        #
        # Refresh if expired (or about to expire)
        #
        if self._token is None or time.time() >= self._expiry - 300:
            self._authenticate()

        return self._token

    ####################################################################
    # Internal
    ####################################################################

    def _authenticate(self):

        response = requests.post(
            self.AUTH_URL,
            json={
                "email": self.email,
                "password": self.password,
            },
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        self._token = data["access_token"]
        self._expiry = int(data["expiry_timestamp"])

        print(f"Fetched OneMap token. Expires at {self._expiry}")
