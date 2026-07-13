import json
from pprint import pprint
from services.lta_service import LTADataMallClient
from services.traffic_service import TrafficService


def showcase_incident_objects():
    # 1. Initialize client and service
    client = LTADataMallClient()
    service = TrafficService(client)

    print("Fetching and building TrafficIncident objects...\n")
    incidents = service.fetch_live_incidents()

    if not incidents:
        print("No active traffic incidents found at the moment.")
        return

    # 2. Pick the first incident object to inspect
    first_incident = incidents[0]

    print("=" * 60)
    print("1. RAW PYTHON OBJECT REPRESENTATION (__repr__)")
    print("=" * 60)
    print(first_incident)
    print("\n" + "=" * 60)

    print("2. SERIALIZED OBJECT DICTIONARY (Data Field View)")
    print("=" * 60)
    # If using Pydantic v2, use .model_dump(). If Pydantic v1, use .dict()
    # If it's a standard dataclass, use dataclasses.asdict(first_incident)
    try:
        object_data = first_incident.model_dump()
    except AttributeError:
        try:
            object_data = first_incident.dict()
        except AttributeError:
            import dataclasses

            object_data = dataclasses.asdict(first_incident)

    # Print the dictionary cleanly with indentation
    print(json.dumps(object_data, indent=4, default=str))
    print("=" * 60)


if __name__ == "__main__":
    showcase_incident_objects()
