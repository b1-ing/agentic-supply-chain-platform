# Graph Report - .  (2026-07-14)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 294 nodes · 533 edges · 17 communities (15 shown, 2 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 67 edges (avg confidence: 0.6)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5f1cf610`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- RoutingLocation
- LTADataMallClient
- test_order_pipeline.py
- main.py
- TomTomTileService
- ConstraintRepository
- graph.py
- Vehicle
- RouteStop
- assessment.py
- WeatherService
- RoutingService
- agentic-supply-chain-platform

## God Nodes (most connected - your core abstractions)
1. `LTADataMallClient` - 18 edges
2. `RoutingLocation` - 18 edges
3. `LTATrafficService` - 13 edges
4. `TrafficService` - 13 edges
5. `OrderState` - 12 edges
6. `WorldState` - 12 edges
7. `IncomingOrder` - 11 edges
8. `Vehicle` - 11 edges
9. `MatrixService` - 11 edges
10. `TomTomTileService` - 11 edges

## Surprising Connections (you probably didn't know these)
- `TrafficAgent` --uses--> `LTATrafficService`  [INFERRED]
  agents/traffic_agent.py → services/lta_service.py
- `WorkflowState` --uses--> `WorldState`  [INFERRED]
  workflow/state.py → models/world_state.py
- `RoutingWorkflow` --uses--> `RoadMatcher`  [INFERRED]
  workflow/routing_workflow.py → services/road_matcher.py
- `RoutingWorkflow` --uses--> `TrafficService`  [INFERRED]
  workflow/routing_workflow.py → services/traffic_service.py
- `PlanningAgent` --uses--> `MatrixService`  [INFERRED]
  agents/planning_agent.py → routing/matrix_service.py

## Import Cycles
- None detected.

## Communities (17 total, 2 thin omitted)

### Community 0 - "RoutingLocation"
Cohesion: 0.08
Nodes (31): PlanningAgent, graph, RoutingLocation, Pairwise travel-time matrix.      matrix[i][j] is the travel time from     lo, TravelMatrix, MatrixService, Compute an NxN travel-time matrix over the supplied routing locations., ORToolsSolver (+23 more)

### Community 1 - "LTADataMallClient"
Cohesion: 0.09
Nodes (14): TrafficAgent, Event, RoadSpeedObservation, TrafficIncident, ContextBuilder, LTADataMallClient, Any, Handles the 500-record pagination limit automatically via OData ?$skip (+6 more)

### Community 2 - "test_order_pipeline.py"
Cohesion: 0.14
Nodes (19): assess_order(), OrderExtractionAgent, geocode_order(), snap_to_graph(), store_order(), validate_order(), build_order_graph(), IncomingOrder (+11 more)

### Community 3 - "main.py"
Cohesion: 0.09
Nodes (22): bootstrap(), create_combined_dashboard(), draw_tile_grid(), main(), plot_tomtom_segments_instantly(), Generates an interactive Leaflet map overlaying tiles and graph costs., Converts raw parsed TomTom traffic segments into a GeoJSON feature collection, Standard Google OR-Tools CVRP Execution Loop. (+14 more)

### Community 4 - "TomTomTileService"
Cohesion: 0.11
Nodes (14): Path, _json_default(), _json_object_hook(), Any, TTLCache, MultiDiGraph, Decode raw PBF tile bytes into a list of segment dicts., Fetch a single TomTom flow tile, transparently read-through cached.          C (+6 more)

### Community 5 - "ConstraintRepository"
Cohesion: 0.12
Nodes (8): ConstraintAction, ConstraintEngine, Enum, RoutingConstraint, ConstraintRepository, OSMService, test_graph_loading(), RoutingWorkflow

### Community 6 - "graph.py"
Cohesion: 0.16
Nodes (11): TODO         Version 1:             return nearest edge          Version 2:, RoadMatcher, TypedDict, build_workflow(), constraint_node(), context_node(), graph_node(), GraphBuilder (+3 more)

### Community 7 - "Vehicle"
Cohesion: 0.23
Nodes (10): ABC, BaseModel, Enum, str, HazmatTruck, RefrigeratedTruck, StandardTruck, HazmatTruck (+2 more)

### Community 8 - "RouteStop"
Cohesion: 0.23
Nodes (7): RoutePlan, RouteSegment, RouteStop, VehicleRoute, RouteBuilder, TravelMatrix, Vehicle

### Community 9 - "assessment.py"
Cohesion: 0.24
Nodes (9): # NOTE: See the crucial tip below regarding local structured outputs, RoutingAgent, IncidentAssessment, PlanningResult, BaseModel, Enum, str, RoadStatus (+1 more)

### Community 10 - "WeatherService"
Cohesion: 0.24
Nodes (6): test_weather_pipeline(), Any, Retrieves the structural schema and metadata for the weather collection., Boilerplate for retrieving the actual live weather values (real-time data)., Initializes the weather service.         Collection ID 1459 targets the data.go, WeatherService

## Knowledge Gaps
- **1 isolated node(s):** `agentic-supply-chain-platform`
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `MatrixService` connect `RoutingLocation` to `main.py`?**
  _High betweenness centrality (0.141) - this node is a cross-community bridge._
- **Why does `RoutingLocation` connect `RoutingLocation` to `RouteStop`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Why does `WorldState` connect `test_order_pipeline.py` to `LTADataMallClient`, `main.py`, `graph.py`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `LTADataMallClient` (e.g. with `TrafficAgent` and `TrafficService`) actually correct?**
  _`LTADataMallClient` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `RoutingLocation` (e.g. with `RouteStop` and `TravelMatrix`) actually correct?**
  _`RoutingLocation` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `TrafficService` (e.g. with `RoadSpeedObservation` and `TrafficIncident`) actually correct?**
  _`TrafficService` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `OrderState` (e.g. with `OrderExtractionAgent` and `build_order_graph()`) actually correct?**
  _`OrderState` has 5 INFERRED edges - model-reasoned connections that need verification._