# CLAUDE.md

> **Status note.** This file documents the **current state of the code**. The project is mid-rewrite — recent commits include *"problem builder for the routing component is still wip"* and *"working on the models for the routing component"*. The design philosophy sections (LLM is for reasoning, services don't mutate the graph, deterministic pipeline must work without LLM) describe the *target* and are load-bearing constraints, but several pieces described in earlier versions of this file (e.g. `WorldState.penalized_graph`, the `replan_needed` short-circuit branch, config-driven penalty mappings) are not yet implemented. See **Known Gaps vs Target** at the end.

---

## Project Overview

This project is an **agentic fleet routing platform** for dynamic vehicle routing under changing operational conditions, currently scoped to **Singapore**.

The system combines:

* **Deterministic optimization** — OSMnx + NetworkX + Google OR-Tools.
* **LLM-based planning / orchestration** — LangChain `ChatOpenAI` with structured outputs, defaulting to a local OpenAI-compatible server.
* **External data sources** — LTA DataMall traffic, TomTom traffic tiles, OneMap geocoding, OSM road graph, weather (NEA).

The LLM **does not compute routes**. It reasons about operational impact and configures the optimization problem.

---

## High-Level Architecture

```
External APIs (LTA, TomTom, NEA, OneMap, OSM)
    │
    ▼
Services
(fetch + normalize, in parallel)
    │
    ▼
WorldState  (single object passed through the workflow)
    │
    ▼
LangGraph workflow
    fetch → match → context → planning → constraint → graph → END
    │
    ▼
RoutingProblemBuilder → MatrixService → OR-Tools Solver → RouteBuilder
    │
    ▼
RoutePlan (per-vehicle stops + segments)
```

**Graph lineage (target).** `WorldState.graph` is the immutable raw OSM graph and is the source of truth. The Graph Builder should produce a derived `WorldState.penalized_graph` per optimize call. In practice the current code mutates `world.graph` in place — see Known Gaps.

---

## Design Principles

### Services

Services only retrieve and normalize data.

They should **never**:

* modify the graph
* create routing penalties
* make optimization decisions

Actual service files in `services/`: `osm_service.py`, `lta_service.py`, `tomtom_service.py`, `traffic_service.py`, `weather_service.py`, `geocode_service.py`, `road_matcher.py`, `problem_builder.py`, `context_builder.py`, `cache.py`.

Only `lta_service.LTATrafficService.sync_network_flow_async` is currently wired into the live execution path (`bootstrap.py`, `workflow/nodes/fetch_node.py`, `agents/traffic_agent.py`).

### RoadMatcher

Lives at `services/road_matcher.py`. Maps lat/lon to candidate graph edges using `osmnx.distance.nearest_edges`. No AI.

> **Gap.** `nearby_edges(lat, lon, radius=100)` currently returns only the single nearest edge regardless of `radius`. A `radius`-aware implementation is a TODO in the file.

### Planning Agent (LLM)

`agents/routing_agent.py` — `RoutingAgent`.

* Uses `ChatOpenAI` with `with_structured_output(PlanningResult, method="json_mode")`.
* Default: local OpenAI-compatible server at `http://localhost:8081/v1`, model `gemini-3.5-flash-thinking`, `temperature=0.0`.
* Pass `use_local=False` to switch to `gpt-4.1`.
* `evaluate(context) → PlanningResult(assessments, recommend_replan, summary)`.

Responsibilities:

* assess operational significance of matched traffic incidents
* classify severity (`LOW` / `MEDIUM` / `HIGH` / `CRITICAL`) and road status (`OPEN` / `PARTIAL` / `CLOSED`)
* estimate expected delay
* set `recommend_replan` and emit a `summary`

It does **not**:

* modify graph weights
* call OR-Tools
* compute shortest paths

**Schema validation.** LLM outputs go through Pydantic `PlanningResult` / `IncidentAssessment` (`models/assessment.py`) before any downstream node touches them. A hallucinated field shape breaks the constraint engine silently — never let raw LLM output cross a node boundary unvalidated.

### Constraint Engine

Two implementations exist:

* **`workflow/nodes/constraint_node.py`** — **active**. Reads `world.assessments` and `world.matched_events`, produces a list of `{edges, penalty, closed}` dicts into `world.constraints`. Penalty table is hard-coded at the top of the file:
  ```
  PENALTIES = {"LOW": 25, "MEDIUM": 100, "HIGH": 300, "CRITICAL": 1000}
  ```
  Config loading is a TODO.
* **`models/constraint_engine.py`** — **legacy / not wired in**. Imports a `models.constraints` module that doesn't exist (the actual module is `models/constraint.py`). This is dead code pending cleanup.

### Graph Builder

Lives at `workflow/nodes/graph_node.py`. `GraphBuilder.apply_constraints` mutates the graph in place, setting `routing_cost` on each affected edge. The current logic is:

1. Initialize `routing_cost = travel_time` if not set.
2. If the constraint marks the road closed, set `routing_cost = inf` and `closed = True`.
3. Otherwise, only set `routing_cost = travel_time + penalty` if `travel_time` is *less than* the estimated minimum — a "smart layering" rule that avoids double-charging edges where live traffic has already overtaken the penalty.

> **Gap.** This mutates `world.graph` in place rather than producing a separate `penalized_graph`. The lineage guarantee is not enforced.

### OR-Tools

The solver lives at `routing/or_tools_solver.py`. It is a standard Capacitated VRP:

* `pywrapcp.RoutingIndexManager(len(matrix), len(capacities), starts, ends)` — supports per-vehicle start/end.
* `PATH_CHEAPEST_ARC` first-solution strategy, `GUIDED_LOCAL_SEARCH` metaheuristic, 10s time limit (configurable).
* Single dimension: `AddDimensionWithVehicleCapacity` keyed on the demand callback.
* Returns `list[list[int]]` of matrix indices per vehicle, or `None` on infeasibility.

> The legacy `main.py` also has a hand-rolled CVRP loop using a single shared depot — kept for reference; the active path goes through `ORToolsSolver`.

---

## WorldState

The workflow passes around a single `WorldState` object, wrapped in `WorkflowState = TypedDict(world=WorldState)` (`workflow/state.py`).

**Actual fields** (from `models/world_state.py`):

| Field | Type | Notes |
|---|---|---|
| `graph` | `nx.MultiDiGraph` | OSM road graph; treated as immutable in spirit, mutated in practice. |
| `mapping` | `dict` | LTA→OSM segment mapping loaded from `cache/lta_osm_mapping.json`. |
| `traffic_events` | `list[TrafficIncident]` | From `fetch_node`. |
| `matched_events` | `list` | From `match_node` — `{"incident": ..., "edges": ...}` dicts. |
| `vehicles` | `list[Vehicle]` | Fleet. Pydantic models, see Routing Subsystem. |
| `orders` | `list[IncomingOrder]` | Customer orders (parsed by the order intake graph). |
| `assessments` | `list` | LLM `IncidentAssessment` list. |
| `constraints` | `list` | `{edges, penalty, closed}` dicts. |
| `routes` | `list` | Set by `RouteBuilder` (currently stored here, not in a sub-field). |
| `recommend_replan` | `bool` | Set by `RoutingAgent`. |
| `summary` | `str` | Set by `RoutingAgent`. |

> **Gap.** The earlier doc described `depots`, `missions`, `penalized_graph`, `last_replan_at`, `replan_needed` as fields. The active counterparts today are `recommend_replan` and `summary` (in place of `replan_needed`); the others are not yet modeled.

---

## LangGraph Workflows

Three graphs exist; one is empty.

### 1. Replanning pipeline — `workflow/graph.py`

`WorkflowState` → `WorldState` is the only state field.

```
fetch → match → context → planning → constraint → graph → END
```

All edges are unconditional. The node functions are thin wrappers that mutate `world` and return `{"world": world}`.

| Node | File | Job |
|---|---|---|
| `fetch` | `workflow/nodes/fetch_node.py` | Fetch live LTA incidents into `world.traffic_events`. |
| `match` | `workflow/nodes/match_node.py` | Map each incident to graph edges via `RoadMatcher` → `world.matched_events`. |
| `context` | `workflow/nodes/context_node.py` | Project `matched_events` into a compact `[{type, message, edges}]` list → `world.context`. |
| `planning` | `workflow/nodes/routing_assessment_node.py` | Run `RoutingAgent.evaluate(world.context)` → `world.assessments`, `world.recommend_replan`, `world.summary`. |
| `constraint` | `workflow/nodes/constraint_node.py` | Pair assessments with matched events → `world.constraints`. |
| `graph` | `workflow/nodes/graph_node.py` | `GraphBuilder.apply_constraints` mutates `world.graph` edges in place. |

> **Gap.** The `recommend_replan == False → END` short-circuit described in earlier versions of this doc is not yet wired. The graph always runs the full pipeline.

### 2. Order intake — `graphs/order_graph.py`

`OrderState` (`models/order_state.py`) carries `raw_order`, parsed `order: IncomingOrder`, shared `world: WorldState`, and diagnostics.

```
validate_order → geocode → store_order
       ▲            │
       └─ assess_order (loop)
```

Node files in `graphs/nodes/order/`: `validate_order.py`, `assess_order.py`, `geocode.py`, `snap_to_graph.py`, `store_order.py`. (The `snap_to_graph` node is registered in the import list but not yet wired into the edges — TODO.)

### 3. Planning — `graphs/planning_graph.py`

Empty file. WIP.

### LangSmith tracing

Several nodes are decorated with `@traceable(name=...)` (currently commented out in `fetch_node.py`, active in `match_node.py` and `routing_assessment_node.py`). Tracing is opt-in; flip the comment to enable.

---

## Routing Subsystem

The post-`graph` solve path is the routing subsystem. It is the part of the code most actively in flux — `problem_builder.py` and the `world.vehicles` / `world.orders` wiring are still WIP per `bf196b1`.

### `services/problem_builder.py` — `RoutingProblemBuilder`

Builds a `RoutingProblem` from `WorldState`:

1. **`_select_vehicles`** — filters `world.vehicles` to `VehicleStatus.IDLE` only.
2. **`_build_locations`** — emits a list of `RoutingLocation`s in order: all depots first (from `world.depots`), then for each `order` a `pickup` and a `delivery`. Each location is assigned a sequential `matrix_index`.
3. **`_build_starts` / `_build_ends`** — currently all vehicles share the first depot's index.
4. **`_build_capacities`** — `int(vehicle.max_weight_kg)` per vehicle.
5. **`_build_demands`** — depot = 0; pickup = `+int(order.weight_kg or 0)`; delivery = `-weight` (the classic pickup-and-delivery trick that cancels out at the depot).

> **Gap.** `world.depots` is not yet a field on `WorldState` (see Known Gaps). `_build_depots` will `AttributeError` until it's added.

### `routing/matrix_service.py` — `MatrixService`

* Calls `nx.single_source_dijkstra_path_length(world.graph, source.graph_node, weight="travel_time")` for every source location.
* Returns `TravelMatrix(matrix=ndarray, locations=...)`. `matrix[i][j]` is travel time (seconds-derived units) from `locations[i]` to `locations[j]`.

> **Note.** The matrix service still keys on `weight="travel_time"` rather than `routing_cost` set by `graph_node`. Effectively, planner penalties set by the constraint engine are *not* reflected in the OR-Tools cost matrix in the current code. This is a known limitation; see Known Gaps.

### `routing/or_tools_solver.py` — `ORToolsSolver`

CVRP over the matrix, per-vehicle `starts`/`ends`, demands, capacities. See OR-Tools section above for solver parameters. Returns `list[list[int]]` of matrix indices per vehicle, or `None` on infeasibility.

### `routing/route_builder.py` — `RouteBuilder`

Expands the OR-Tools index list into a `RoutePlan`:

* For each vehicle, walk consecutive stops; for each `(stop_i, stop_{i+1})` pair, run `nx.shortest_path(graph, source=graph_node_i, target=graph_node_{i+1}, weight="travel_time")` to expand to a real path.
* Sum `travel_time` and `length` across edges along the path (uses the lowest-`travel_time` key in the case of `MultiDiGraph`).
* Returns `RoutePlan(routes=[VehicleRoute(...)], total_distance, total_travel_time)`.

### `routing/routing_service.py`

Higher-level wrapper (not yet read in detail; treat as a façade over the four pieces above).

### `models/vehicles/`

`Vehicle` is a Pydantic `BaseModel` + ABC with: `vehicle_id`, `status: VehicleStatus` (IDLE/EN_ROUTE/LOADING/OFFLINE), optional `current_node` / `current_lat` / `current_lon`, plus dimensional limits `max_weight_kg`, `max_volume_m3`, `max_pallets`, `height_m`, `width_m`, `length_m`, and flags `refrigerated`, `hazardous_certified`.

Concrete subclasses:

| Class | `max_weight_kg` | `max_volume_m3` | `max_pallets` | `height_m` | Notes |
|---|---|---|---|---|---|
| `StandardTruck` | 5,000 | 25 | 10 | 3.5 | Default. |
| `TallTruck` | 10,000 | 35 | 16 | 6.0 | Height-sensitive. |
| `HazmatTruck` | 10,000 | 35 | 16 | 4.0 | `hazardous_certified=True`. |
| `RefrigeratedTruck` | 20,000 | 60 | 24 | 4.5 | `refrigerated=True`. |

### `models/assessment.py` — LLM output schema

* `Severity` enum: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
* `RoadStatus` enum: `OPEN`, `PARTIAL`, `CLOSED`.
* `IncidentAssessment`: `incident_index`, `severity`, `road_status`, `expected_delay_minutes`, `affects_routing`, `reason`.
* `PlanningResult`: `assessments: list[IncidentAssessment]`, `recommend_replan: bool`, `summary: str`.

---

## Context Builder

`services/context_builder.py` is the dedicated module for translating `WorldState` into a token-budgeted, model-ready summary. The active `context_node` is a minimal in-line implementation (extracts `type`, `message`, `edges` per matched event); the dedicated module is the place to do real selection / clustering / budget enforcement.

Output target: a `PlanningContext` Pydantic object passed to `RoutingAgent.evaluate`. This node is the most important integration point in the system — get it wrong and the LLM sees stale, lossy, or bloated context.

---

## Caching

Three cache layers, all on disk under `cache/`:

* **OSM graph** — `cache/singapore.graphml`. Built once by `bootstrap.py` (uses `osmnx.graph_from_place("Singapore", network_type="drive")` with `maxheight`, `maxweight`, `maxwidth`, `bridge`, `lanes` extra tags). Slow to build; reused aggressively.
* **LTA→OSM spatial mapping** — `cache/lta_osm_mapping.json`. JSON cache of how LTA traffic segments snap to OSM edges. Consumed by `LTATrafficService.sync_network_flow_async`.
* **Service responses** — small JSON files in `cache/` (e.g. `27946ce7…`, `7fe5e7c0…`). These are content-hashed service-response caches. TTL is per data source — LTA traffic is short (minutes), weather can be longer. `services/cache.py` exists as a generic helper; explicit per-service cache modules are still TODO.

> **Gap.** The optional "cache LLM assessments by content-hash of the planning context" layer from earlier docs is not yet implemented.

Every cache must declare its TTL and invalidation trigger. Silent caches are debugging hazards.

---

## Concurrency

* **Service fetches** fan out in parallel and join at the Fetch Node — never serialize independent external calls. (The current `fetch_node` is sequential, but the design holds for future multi-service fan-out.)
* **Graph Builder + OR-Tools optimize** is single-threaded per workflow run by design (one solve at a time, deterministic). Multiple concurrent replans run as separate workflow invocations against the same cached graph.
* **`agents/traffic_agent.py`** is an `asyncio` loop that ticks every `update_interval=60s` and mutates `world.graph` in place via `LTATrafficService.sync_network_flow_async`. This loop is the practical way live traffic enters the system today. See Known Gaps — it bypasses the graph-lineage rule.

---

## Failure Modes and Fallback

The deterministic pipeline must remain fully functional if the LLM is unavailable. Concretely:

* **Planning Agent call fails or times out.** Fallback: empty `assessments` list. `constraint_node` produces empty constraints. `graph_node` leaves the graph untouched. `MatrixService` + `ORToolsSolver` still run on the raw graph with only static vehicle/mission constraints.
* **Constraint Engine produces an empty constraint set.** `graph_node` returns `graph` unchanged. Optimize proceeds normally.
* **OR-Tools returns `None`** (infeasible). Surface the infeasibility diagnosis to the caller; do not retry silently with mutated inputs. `ORToolsSolver.solve` already returns `None` cleanly.
* **Service unavailable.** Skip that service's data layer, log the failure, continue with remaining sources. The deterministic pipeline must keep producing routes.

Every fallback must be tested explicitly. "Works without LLM" is a property, not a hope.

---

## Observability

LLM calls are non-deterministic, expensive, and a debugging nightmare without logs. Required instrumentation:

* per-node latency and token usage
* raw LLM I/O (prompt + completion) with correlation IDs
* constraint engine decisions (assessment → penalty mapping) recorded as structured events
* optimize run duration, gap to best-known, feasibility status

`@traceable` decorators from `langsmith` are already in place on several nodes; most are commented out. Pick a tracing tool later — the requirement is that it exists, not which one. Cheap to add now, expensive to retrofit.

---

## Testing

Test files live in `tests/` and mirror four layers:

| Layer | Files | Purpose |
|---|---|---|
| **Constraint / golden** | `test_problem_builder.py`, `test_road_matcher.py` | Pure functions, table-driven checks. (Severity → penalty golden tests for `constraint_node` itself are still TODO — see Known Gaps.) |
| **Pipeline regression** | `test_order_pipeline.py`, `run_matrix_demo.py` | End-to-end runs with frozen mocks. |
| **Planning Agent snapshot** | `test_planning_agent.py` | Validated structured output for canonical scenarios. |
| **OR-Tools feasibility** | `test_ortools_solver.py` | Small CVRP instances with known optima. |
| **Service / live** | `test_lta_live.py`, `test_lta_raw.py` (`services/`), `test_tomtom_api_key.py` | Live or near-live data sanity checks. |
| **Debug / scratch** | `debug_tomtom_tile.py`, `test_show_incidents.py`, `test_matrix_service.py` | Not part of CI; used during development. |

---

## Cargo and Vehicle Constraints

Routing should consider:

**Vehicle** — capacity, weight, height, hazardous certification, vehicle type. Encoded on the `Vehicle` Pydantic model and the four concrete subclasses above.

**Mission / order** — cargo type, cargo weight, priority, deadlines. Encoded on `IncomingOrder` (`models/incoming_state.py`): `weight_kg`, `volume_m3`, `pallets`, `refrigerated`, `hazardous`, `fragile`, `oversized`, and `earliest_pickup` / `latest_pickup` / `earliest_delivery` / `latest_delivery` time windows (as ISO strings).

**Road** — height limits, weight limits, hazardous cargo restrictions, temporary closures, traffic penalties. Intrinsic OSM edge tags (loaded by `bootstrap.py` into `maxheight`, `maxweight`, `maxwidth`, `bridge`, `lanes`) plus dynamic `routing_cost` and `closed` flags written by `graph_node`.

**Placement.** Vehicle and order attributes are static data carried in `WorldState.vehicles` and `WorldState.orders` and consumed directly by `RoutingProblemBuilder` / `ORToolsSolver`. They do not pass through the Planning Agent or Constraint Engine. Road attributes (height / weight / hazardous) are intrinsic to the OSM graph edges and would be consumed by the Graph Builder when constructing a future `penalized_graph`. Only *dynamic* road conditions (temporary closures, traffic penalties) are produced by the Constraint Engine from Planning Agent assessments.

---

## Development Priorities

1. Complete deterministic pipeline (problem builder wiring against `WorldState.depots` and `WorldState.orders`).
2. Enforce graph lineage (`penalized_graph` derived per optimize call).
3. Add conditional `recommend_replan` short-circuit to the LangGraph graph.
4. Move the `PENALTIES` table out of source into a config file.
5. Add additional data sources (NEA weather is scaffolded; OneMap geocode is scaffolded).
6. Add explanation agent.

The deterministic pipeline must remain fully functional even if the LLM is unavailable.

---

## Known Gaps vs Target

Honest list of things this doc previously described as done-but-aren't (or that diverge from the target). Each is a small, well-scoped piece of work.

* **`WorldState` is missing fields.** `depots`, `penalized_graph`, `missions`, `last_replan_at`, `replan_needed` are not modeled. Active counterparts today: `recommend_replan` and `summary`. `_build_depots` in `problem_builder.py` will `AttributeError` until `depots` is added.
* **No `recommend_replan` short-circuit.** `workflow/graph.py` runs the full chain unconditionally. The conditional `END` edge is not wired.
* **Graph lineage is not enforced.** `graph_node.GraphBuilder.apply_constraints` and `agents/traffic_agent.TrafficAgent.sync_traffic` both mutate `world.graph` in place rather than producing a derived `penalized_graph`.
* **`RoadMatcher.nearby_edges` ignores its `radius` argument.** Returns only `nearest_edge`. A radius-aware version is a TODO in the file.
* **`PENALTIES` is hard-coded** at the top of `workflow/nodes/constraint_node.py`. Config loading is TODO.
* **`models/constraint_engine.py` is dead code.** Imports `models.constraints` (which doesn't exist; the actual file is `models/constraint.py`). It is not wired into the graph — `workflow/nodes/constraint_node.py` is.
* **`graphs/planning_graph.py` is empty.**
* **`graphs/order_graph.py` is partially wired.** `graphs/nodes/order/snap_to_graph.py` is imported but not connected in the edge list.
* **`agents/planning_agent.py` is misnamed.** Despite the name, it is a *routing-solver wrapper* (`CompatibilityService` → `LocationBuilderService` → `MatrixService` → `ORToolsSolver`) and is not the LLM planning agent. The LLM agent is `agents/routing_agent.py` (`RoutingAgent`).
* **`workflow/routing_workflow.py` is stale.** Imports `engine.constraint_engine` and `services.osm_service` in a way that doesn't match the rest of the code. It is not invoked by `main.py`.
* **`MatrixService` keys on `travel_time`, not `routing_cost`.** Planner penalties set by `graph_node` are not reflected in the OR-Tools cost matrix today. The plan was to consume `routing_cost`.
* **Constraint golden tests are missing.** The four-layer test plan in the Testing section above lists severity→penalty golden tests as required, but `tests/` doesn't have one for `constraint_node` yet.
* **`@traceable` decorators are mostly commented out** in `workflow/nodes/`. Observability wiring is half-done.

---

## Roadmap (Out of Scope for v1)

Future nodes / capabilities, listed here so v1 stays unambiguous:

* Weather Agent
* Mission Agent
* Vehicle Agent
* Explanation Agent
* Multi-vehicle simulation harness
* Live telemetry integration

---

## Guiding Principle

Use LLMs for **decision making and orchestration**.

Use deterministic algorithms for **routing and optimization**.

---

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
