# test_lta_live.py
import os
import sys
from pprint import pprint

# Ensure Python can resolve paths relative to the current working environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from services.lta_service import LTADataMallClient
except ImportError as e:
    print(
        f"[-] Import Error: Make sure this file is placed right outside the services directory. Details: {e}"
    )
    sys.exit(1)


def test_live_connection():
    print("==================================================")
    print("[*] Initializing LTA Client from lta_service.py...")
    print("==================================================")

    try:
        # 1. Initialize client. It will automatically load the key via your load_dotenv() setup
        client = LTADataMallClient()

        # Verify which key string pattern is being loaded securely
        masked_key = f"{client.account_key[:6]}..." if client.account_key else "None"
        print(f"[+] Client initialized with key snippet: {masked_key}")

        # 2. Query the live dynamic TrafficIncidents endpoint
        endpoint = "TrafficIncidents"
        print(f"[*] Dispatching request to live endpoint: /{endpoint}...")

        raw_records = client.fetch_all_pages(endpoint)

        print("\n==================================================")
        print("[+] SUCCESS! API connection established.")
        print(f"[+] Total live records fetched across all pages: {len(raw_records)}")
        print("==================================================")

        if raw_records:
            print("\n[*] Inspecting raw structural payload layout (First 2 records):")
            print("--------------------------------------------------")
            pprint(raw_records[:2])
            print("--------------------------------------------------")
        else:
            print(
                "\n[!] Connection successful, but the LTA payload array is currently empty."
            )
            print(
                "    (This can happen if there are no active road incidents in Singapore right now)."
            )

    except ValueError as val_err:
        print(f"\n[-] Configuration Error: {val_err}")
        print("    Check that your .env file contains: LTA_ACCOUNT_KEY=your_actual_key")

    except Exception as e:
        print(f"\n[-] Connection Pipeline Failed: {e}")


if __name__ == "__main__":
    test_live_connection()
