# config.py

import os
from dotenv import load_dotenv

load_dotenv()

VALHALLA_URL = os.getenv("VALHALLA_URL", "http://localhost:8002")
VALHALLA_TIMEOUT = int(os.getenv("VALHALLA_TIMEOUT", "30"))
