# test_planning_agent.py
import sys
import os

# Safe guard: Ensures Python can see the root directory for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ---- IMPORT YOUR ENTIRE PRODUCTION PIPELINE ----
from services.lta_service import LTADataMallClient
from services.traffic_service import TrafficService
from agents.planning_agent import PlanningAgent
from models.assessment import PlanningResult


def run_live_traffic_agent_test():
    print("\n" + "=" * 60)
    print("INITIALIZING LIVE TRAFFIC CONTEXT INTEGRATION TEST")
    print("=" * 60)

    # 1. Initialize the live LTA DataMall ingestion pipeline
    print("[*] Connecting to LTA DataMall Service...")
    try:
        client = LTADataMallClient()
        traffic_service = TrafficService(client)
        print("[+] Traffic service ingestion layers online.")
    except Exception as e:
        print(f"[-] Failed to setup traffic data client: {e}")
        return

    # 2. Initialize your local planning agent engine
    try:
        agent = PlanningAgent()  # Defaults to your local localhost:8081 server
    except Exception as e:
        print(f"[-] Connection Error: Could not reach local model server on 8081. {e}")
        return

    # 3. Pull live streaming incident text feeds from Singapore's roads
    print("[*] Fetching current active street incident feeds...")
    live_incidents = traffic_service.fetch_live_incidents()

    if not live_incidents:
        print(
            "✅ System Stable: There are no active incidents on the network right now."
        )
        print(
            "💡 Tip: Try testing again later when road conditions update, or mock temporary text."
        )
        return

    print(f"[+] Successfully extracted {len(live_incidents)} real-time incidents.")
    print("-" * 60)

    # 4. Loop over the live feeds and pass them directly to the cognitive agent
    # We slice live_incidents[:3] to analyze up to 3 active feeds so your console output stays clean
    for idx, incident in enumerate(live_incidents[:3], 1):
        print(f"\n[*] Evaluating Live Incident #{idx} ({incident.incident_type})")
        print(f"    Raw Text Feed: '{incident.message}'")
        print("    Processing through local agent...")

        try:
            # We bridge the pipeline here: Pass the real LTA message string straight into your agent
            output: PlanningResult = agent.evaluate(incident.message)

            print("\n  🔍 AGENT STRUCTURED ASSESSMENT:")
            print(f"  ├── Severity:         {output.severity.upper()}")
            print(f"  ├── Road Status:      {output.road_status}")
            print(f"  ├── Estimated Delay:  {output.estimated_delay}")
            print(f"  ├── Affects Routing:  {output.affects_routing}")
            print(
                f"  └── SHOULD REPLAN:    {output.recommend_replan}  "
                f"{'🚨 [TRIGGERING ROUTING ENGINE OVERHAUL]' if output.recommend_replan else '✅ [KEEP PATH]'}"
            )

        except Exception as e:
            print(f"  ❌ Runtime Parsing Error on this feed: {e}")

    print("\n" + "=" * 60)
    print("[+] Integration Test Completed Successfully.")


if __name__ == "__main__":
    run_live_traffic_agent_test()
