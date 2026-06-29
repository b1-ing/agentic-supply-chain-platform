import io
import json
import zipfile
import requests
from pprint import pprint

def test_static_roadworks():
    url = "https://datamall.lta.gov.sg/content/dam/datamall/datasets/TrafficRelated/RoadWorks.zip"

    print("==================================================")
    print(f"[*] Downloading static asset from:\n    {url}")
    print("==================================================")

    try:
        response = requests.get(url, timeout=20)

        if response.status_code == 200:
            print("[+] Download complete! Processing zip archive in memory...")

            zip_buffer = io.BytesIO(response.content)

            with zipfile.ZipFile(zip_buffer) as the_zip:
                file_list = the_zip.namelist()
                print(f"[+] Files found inside archive: {file_list}")

                # FIX: Look specifically for the JSON file instead of taking index 0
                target_filename = next((f for f in file_list if f.endswith('.json')), None)

                if not target_filename:
                    print("[-] Error: Could not find a .json file inside the zip archive.")
                    return

                print(f"[*] Extracting and parsing: {target_filename}...")
                with the_zip.open(target_filename) as json_file:
                    raw_text = json_file.read().decode("utf-8")
                    data = json.loads(raw_text)

            print("\n[+] SUCCESS! JSON successfully extracted and parsed.")

            # Inspect structure layout
            if isinstance(data, dict):
                print(f"Top-level document schema keys: {list(data.keys())}")
                for key, val in data.items():
                    if isinstance(val, list) and len(val) > 0:
                        print(f"\n[*] Previewing first raw record under key '{key}':")
                        pprint(val[0])
                        break
            elif isinstance(data, list) and len(data) > 0:
                print(f"Total entries found in top-level array: {len(data)}")
                print("\n[*] Previewing first raw record from array:")
                pprint(data[0])

        else:
            print(f"[-] HTTP Request Failed. Status Code: {response.status_code}")

    except Exception as e:
        print(f"\n[-] Pipeline Error: {e}")

if __name__ == "__main__":
    test_static_roadworks()