# CLAUDE.md

## Project Overview

This project is an **agentic fleet routing platform** for dynamic vehicle routing under changing operational conditions.

The system combines:

* Deterministic optimization (OSMnx + NetworkX + OR-Tools)
* LLM-based planning/orchestration
* External data sources (LTA DataMall, weather, vehicle telemetry, etc.)

The LLM **does not compute routes**. It reasons about operational impact and configures the optimization problem.

---

# High-Level Architecture

```
External APIs
    │
    ▼
Services
(fetch + normalize, in parallel)
    │
    ▼
WorldState
    │
    ▼
RoadMatcher
    │
    ▼
Planning Agent (LLM)
    │
    ▼
Constraint Engine
    │
    ▼
Graph Builder
    │
    ▼
OR-Tools Fleet Optimizer
    │
    ▼
Fleet Routes
```

**Graph lineage.** `WorldState.graph` is the immutable raw OSM graph and is the source of truth. The Graph Builder produces a derived `WorldState.penalized_graph` per optimize call. Never mutate `WorldState.graph` in place — the raw graph is reused across replans and across scenarios.

---

# Design Principles

## Services

Services only retrieve and normalize data.

They should **never**:

* modify the graph
* create routing penalties
* make optimization decisions

Examples:

* TrafficService
* WeatherService
* VehicleService
* MissionService

---

## RoadMatcher

Responsible only for mapping geographic events onto OSM road edges.

Input:

* latitude
* longitude

Output:

* candidate graph edges

No AI.

---

## Planning Agent

The Planning Agent is the primary LLM component.

Responsibilities:

* assess operational significance
* determine incident severity
* estimate delays
* determine whether replanning is required

It does **not**:

* modify graph weights
* call OR-Tools
* compute shortest paths

It returns structured assessments only.

---

## Constraint Engine

Deterministic, fully unit-testable code.

Converts semantic assessments into routing constraints.

Example mapping:

```
LOW      -> +25 penalty
MEDIUM   -> +100
HIGH     -> +300
CRITICAL -> +1000
CLOSED   -> remove edge / prohibit traversal
```

Penalty mappings are loaded from config; the constraint engine has no hard-coded values.

---

## Graph Builder

Applies constraints to the NetworkX graph.

Only this component mutates edge weights.

---

## OR-Tools

Responsible for solving the fleet routing problem.

It receives:

* updated graph
* vehicles
* missions
* capacities
* time windows
* constraints

The LLM never performs optimization.

---

# WorldState

The workflow passes around a single `WorldState` object.

It should contain:

* graph (immutable raw OSM graph)
* penalized_graph (derived per optimize call by the Graph Builder)
* traffic_events
* matched_events
* vehicles
* missions
* assessments
* constraints
* routes
* last_replan_at
* replan_needed (set by Planning Agent)

Avoid passing many independent state variables.

`graph` is treated as immutable — never mutate it in place. Always derive a new `penalized_graph` from it. This keeps the raw graph reusable across replans and scenarios, and makes lineage / debugging tractable.

---

# LangGraph Workflow

Current workflow:

```
START

↓

Fetch Node (services fan out in parallel, join at the node)

↓

RoadMatcher Node

↓

Context Builder

↓

Planning Agent

↓       (replan_needed?)

[yes] → Constraint Engine → Graph Builder → Optimizer → END

[no]  → END
```

The Planning Agent returns a `replan_needed` flag in its structured output. When false, the workflow short-circuits to END with the existing routes preserved. Replans are triggered by:

* event-driven: significant new incident classified as MEDIUM+ by the Planning Agent
* periodic: scheduled replan tick (configurable interval)
* on-demand: external caller request

---

# Agent Philosophy

Agents perform **reasoning**, not computation.

Good agent tasks:

* Should the fleet be replanned?
* Which incidents matter?
* How severe is an incident?
* Which missions are affected?
* How should the optimization problem change?

Poor agent tasks:

* shortest paths
* graph search
* edge matching
* CVRP solving
* NetworkX operations

**Schema validation.** LLM outputs must be validated against a Pydantic schema before being trusted by downstream components. A hallucinated field shape breaks the constraint engine silently — never let raw LLM output cross a node boundary unvalidated.

---

# Context Builder

The Context Builder is the bridge between `WorldState` and the Planning Agent's LLM prompt. Its job is to translate large structured state into a token-budgeted, model-ready summary.

Responsibilities:

* select which events / missions / vehicles are relevant (full state is too large to pass to the LLM)
* compress geographic and numeric data where useful (e.g. cluster nearby incidents)
* stay within a configurable token budget
* produce both a structured prompt payload and a human-readable summary string

Output is a `PlanningContext` Pydantic object passed to the Planning Agent. This node is the most important integration point in the system — get it wrong and the LLM sees stale, lossy, or bloated context.

---

# Caching

Three cache layers, with explicit TTLs and invalidation rules:

* **OSM graph.** Slow to build. Keyed by geographic extent. Reused aggressively across all replans and scenarios. Currently at `cache/singapore.graphml`.
* **Service responses.** TTL per data source — e.g. LTA traffic is short (minutes), weather can be longer. Invalidate on explicit refresh requests.
* **LLM assessments.** Optional. Cache by content-hash of the planning context to avoid re-asking the LLM on identical state.

Every cache must declare its TTL and invalidation trigger. Silent caches are debugging hazards.

---

# Concurrency

Service fetches fan out in parallel and join at the Fetch Node — never serialize independent external calls. The Graph Builder + OR-Tools optimize step is single-threaded per workflow run by design (one solve at a time, deterministic). If multiple replans are needed concurrently, run them as separate workflow invocations against the same cached graph.

---

# Failure Modes and Fallback

The deterministic pipeline must remain fully functional if the LLM is unavailable. Concretely:

* **Planning Agent call fails or times out.** The fallback path produces an empty `assessments` list — the Constraint Engine applies no event-based penalties, and the optimizer runs on the raw graph with only static vehicle/mission constraints.
* **Constraint Engine produces an empty constraint set.** Graph Builder returns `penalized_graph == graph`. Optimize proceeds normally.
* **OR-Tools fails to find a feasible solution.** Surface the infeasibility diagnosis to the caller; do not retry silently with mutated inputs.
* **Service unavailable.** Skip that service's data layer, log the failure, continue with remaining sources.

Every fallback must be tested explicitly. "Works without LLM" is a property, not a hope.

---

# Observability

LLM calls are non-deterministic, expensive, and a debugging nightmare without logs. Required instrumentation:

* per-node latency and token usage
* raw LLM I/O (prompt + completion) with correlation IDs
* constraint engine decisions (assessment → penalty mapping) recorded as structured events
* optimize run duration, gap to best-known, feasibility status

Pick a tracing tool later — the requirement is that it exists, not which one. Cheap to add now, expensive to retrofit.

---

# Testing

Four test layers, all required:

* **Constraint Engine golden tests.** Severity → penalty mappings are pure functions; lock them down with table-driven tests.
* **Pipeline regression tests.** Full workflow run with frozen service mocks and a fixed seed; verify output routes match a snapshot.
* **Planning Agent snapshot tests.** Validated structured output for canonical scenarios (no incidents, single closure, cascading incidents).
* **OR-Tools feasibility tests.** Verify optimizer on known small CVRP instances with known optimal solutions before trusting it on production-shaped problems.

---

# Roadmap (Out of Scope for v1)

Future nodes / capabilities, listed here so v1 stays unambiguous:

* Weather Agent
* Mission Agent
* Vehicle Agent
* Explanation Agent
* Multi-vehicle simulation harness
* Live telemetry integration

---

# Cargo and Vehicle Constraints

Routing should consider:

Vehicle:

* capacity
* weight
* height
* hazardous certification
* vehicle type

Mission:

* cargo type
* cargo weight
* priority
* deadlines

Road:

* height limits
* weight limits
* hazardous cargo restrictions
* temporary closures
* traffic penalties

These are deterministic optimization constraints, not LLM decisions.

**Placement.** Vehicle and mission attributes are static data carried in `WorldState.vehicles` and `WorldState.missions` and consumed directly by the OR-Tools optimizer. They do not pass through the Planning Agent or Constraint Engine. Road attributes (height limits, weight limits, hazardous restrictions) are intrinsic to the OSM graph edges and consumed by the Graph Builder when constructing the penalized graph. Only *dynamic* road conditions (temporary closures, traffic penalties) are produced by the Constraint Engine from Planning Agent assessments.

This split keeps the Constraint Engine's scope clear and prevents the Graph Builder from becoming a bottleneck for vehicle-feasibility logic.

---

# Development Priorities

1. Complete deterministic pipeline.
2. Integrate Planning Agent.
3. Add OR-Tools fleet optimization.
4. Add additional data sources.
5. Add explanation agent.

The deterministic pipeline must remain fully functional even if the LLM is unavailable.

---

# Guiding Principle

Use LLMs for **decision making and orchestration**.

Use deterministic algorithms for **routing and optimization**.
