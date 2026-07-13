# Graph Report - D:\code repos\agentic-supply-chain-platform  (2026-07-11)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 279 nodes · 526 edges · 17 communities (15 shown, 2 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 64 edges (avg confidence: 0.61)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4ab047be`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- LTADataMallClient
- RoutingLocation
- TrafficService
- test_order_pipeline.py
- TomTomTileService
- test_planning_agent.py
- Vehicle
- graph.py
- WeatherService
- constraint.py
- RoutingService
- agentic-supply-chain-platform

## God Nodes (most connected - your core abstractions)
1. `LTADataMallClient` - 26 edges
2. `TrafficService` - 19 edges
3. `RoutingLocation` - 16 edges
4. `MatrixService` - 13 edges
5. `LTATrafficService` - 13 edges
6. `TomTomTileService` - 13 edges
7. `OrderState` - 12 edges
8. `WorldState` - 12 edges
9. `IncomingOrder` - 11 edges
10. `Vehicle` - 11 edges

## Surprising Connections (you probably didn't know these)
- `PlanningAgent` --uses--> `MatrixService`  [INFERRED]
  agents/planning_agent.py → routing/matrix_service.py
- `run_live_traffic_agent_test()` --calls--> `PlanningAgent`  [INFERRED]
  test_planning_agent.py → agents/planning_agent.py
- `RoutingAgent` --uses--> `PlanningResult`  [INFERRED]
  agents/routing_agent.py → models/assessment.py
- `TrafficAgent` --uses--> `LTADataMallClient`  [INFERRED]
  agents/traffic_agent.py → services/lta_service.py
- `TrafficAgent` --uses--> `LTATrafficService`  [INFERRED]
  agents/traffic_agent.py → services/lta_service.py

## Import Cycles
- None detected.

## Communities (17 total, 2 thin omitted)

### Community 0 - "LTADataMallClient"
Cohesion: 0.07
Nodes (29): TrafficAgent, bootstrap(), create_combined_dashboard(), draw_tile_grid(), main(), plot_tomtom_segments_instantly(), Generates an interactive Leaflet map overlaying tiles and graph costs., Converts raw parsed TomTom traffic segments into a GeoJSON feature collection (+21 more)

### Community 1 - "RoutingLocation"
Cohesion: 0.09
Nodes (30): graph, Represents a location that participates in routing.     The order of these obje, RoutingLocation, Pairwise travel-time matrix.      matrix[i][j] is the travel time from     lo, TravelMatrix, MatrixService, Compute an NxN travel-time matrix over the supplied routing locations., ORToolsSolver (+22 more)

### Community 2 - "TrafficService"
Cohesion: 0.08
Nodes (16): ConstraintEngine, Event, RoadSpeedObservation, TrafficIncident, ConstraintRepository, ContextBuilder, OSMService, TODO         Version 1:             return nearest edge          Version 2: (+8 more)

### Community 3 - "test_order_pipeline.py"
Cohesion: 0.12
Nodes (21): assess_order(), OrderExtractionAgent, geocode_order(), snap_to_graph(), store_order(), validate_order(), build_order_graph(), IncomingOrder (+13 more)

### Community 4 - "TomTomTileService"
Cohesion: 0.11
Nodes (15): main(), Debug helper: dump raw TomTom features from a single tile so you can see what t, Path, _json_default(), _json_object_hook(), Any, TTLCache, MultiDiGraph (+7 more)

### Community 5 - "test_planning_agent.py"
Cohesion: 0.17
Nodes (11): PlanningAgent, # NOTE: See the crucial tip below regarding local structured outputs, RoutingAgent, IncidentAssessment, PlanningResult, BaseModel, Enum, str (+3 more)

### Community 6 - "Vehicle"
Cohesion: 0.23
Nodes (10): ABC, BaseModel, Enum, str, HazmatTruck, RefrigeratedTruck, StandardTruck, HazmatTruck (+2 more)

### Community 7 - "graph.py"
Cohesion: 0.26
Nodes (8): build_workflow(), constraint_node(), context_node(), fetch_node(), graph_node(), GraphBuilder, match_node(), planning_node()

### Community 8 - "WeatherService"
Cohesion: 0.24
Nodes (6): test_weather_pipeline(), Any, Retrieves the structural schema and metadata for the weather collection., Boilerplate for retrieving the actual live weather values (real-time data)., Initializes the weather service.         Collection ID 1459 targets the data.go, WeatherService

### Community 9 - "constraint.py"
Cohesion: 0.50
Nodes (3): ConstraintAction, Enum, RoutingConstraint

## Knowledge Gaps
- **1 isolated node(s):** `agentic-supply-chain-platform`
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MatrixService` connect `RoutingLocation` to `LTADataMallClient`, `test_planning_agent.py`?**
  _High betweenness centrality (0.144) - this node is a cross-community bridge._
- **Why does `LTADataMallClient` connect `LTADataMallClient` to `TrafficService`, `test_planning_agent.py`, `graph.py`?**
  _High betweenness centrality (0.139) - this node is a cross-community bridge._
- **Why does `WorldState` connect `test_order_pipeline.py` to `LTADataMallClient`, `TrafficService`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `LTADataMallClient` (e.g. with `TrafficAgent` and `TrafficService`) actually correct?**
  _`LTADataMallClient` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `TrafficService` (e.g. with `RoadSpeedObservation` and `TrafficIncident`) actually correct?**
  _`TrafficService` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 6 inferred relationships involving `RoutingLocation` (e.g. with `TravelMatrix` and `MatrixService`) actually correct?**
  _`RoutingLocation` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `MatrixService` (e.g. with `PlanningAgent` and `.__init__()`) actually correct?**
  _`MatrixService` has 5 INFERRED edges - model-reasoned connections that need verification._