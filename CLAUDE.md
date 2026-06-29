# CLAUDE.md

## Project Overview

This project is an **agent-assisted fleet routing platform** designed to generate optimal routes for multiple vehicles while considering dynamic and heterogeneous constraints.

Unlike traditional route planners, the optimization engine is **not AI-driven**. Instead, LLMs are used only where reasoning over unstructured information is required.

The philosophy of this project is:

> **Use AI for reasoning. Use optimization algorithms for optimization.**

---

# High-Level Architecture

```
                    User
                      │
                      ▼
              Mission Definition
                      │
                      ▼
        Data Collection Services
                      │
                      ▼
           Constraint Collection
                      │
                      ▼
           Constraint Engine
      (deterministic business rules)
                      │
          ┌───────────┴────────────┐
          │                        │
      Rules sufficient?          No
          │                        │
          ▼                        ▼
      Continue              LLM Reasoning
          │                        │
          └───────────┬────────────┘
                      ▼
              Graph Construction
                      │
                      ▼
         Google OR-Tools Optimizer
                      │
                      ▼
           Route Validation
                      │
                      ▼
       Monitoring / Replanning
```

---

# Design Principles

## 1. Minimize LLM Usage

LLMs are expensive, slow, and non-deterministic.

They should **never** be responsible for:

* shortest path computation
* graph search
* CVRP solving
* vehicle assignment
* deterministic rule checking

Instead they should only solve problems that are difficult to encode procedurally.

Examples include:

* parsing free-text mission descriptions
* interpreting operator instructions
* extracting constraints from incident reports
* reading regulations
* resolving ambiguous user intent

Everything else should be deterministic Python.

---

## 2. Optimization Is Not AI

Routing is handled by classical optimization algorithms.

Preferred solver:

* Google OR-Tools

Possible future solvers:

* GraphHopper
* OSRM
* NetworkX (prototype)
* Custom optimization algorithms

The optimizer should receive only structured constraints.

It should never receive natural language.

---

## 3. Separate Data Collection from Reasoning

External APIs are wrapped inside Services.

Services should:

* fetch data
* normalize data
* return structured models

Services should NOT:

* make routing decisions
* modify graphs
* call the optimizer
* contain business logic

Example:

```
Traffic API
Government API
Weather API
Bridge Database

↓

TrafficService
WeatherService
BridgeService

↓

Constraint Objects
```

---

# Folder Structure

```
fleet-routing-ai/

services/
    traffic_service.py
    weather_service.py
    bridge_service.py
    vehicle_service.py
    osm_service.py
    regulation_service.py

models/
    constraint.py
    vehicle.py
    mission.py
    road.py

optimizer/
    graph_builder.py
    constraint_engine.py
    ortools_solver.py

agents/
    planner.py
    monitoring.py
    explanation.py

graph/
    workflow.py
    state.py

simulation/

app.py
```

---

# Responsibilities

## Services

Responsible for retrieving data.

Examples:

TrafficService

Returns:

```
Road 52
Delay = 300 seconds
```

RoadClosureService

Returns:

```
Road 81
Status = CLOSED
```

BridgeService

Returns:

```
Bridge
Max Height
Max Weight
```

Services never modify the graph.

---

## Constraint Engine

Responsible for deterministic reasoning.

Examples:

Vehicle height > bridge height

↓

Road forbidden

Road closed

↓

Edge removed

Heavy congestion

↓

Increase edge cost

Most constraints should be processed here.

---

## LLM Reasoning

Only invoked when deterministic rules are insufficient.

Examples:

Input:

```
Avoid residential areas if practical.

Medical convoy.

Highest priority.
```

Output:

```
{
    "priority": "HIGH",
    "avoid": "residential"
}
```

Another example:

Input:

```
Tree fallen.
Small vehicles can still pass.
```

Output:

```
{
    "road": 52,
    "restriction": "small_vehicle_only"
}
```

---

## Graph Builder

Responsible for converting constraints into graph modifications.

Examples:

Road closure

↓

Remove edge

Traffic

↓

Increase edge weight

Height restriction

↓

Remove edge for incompatible vehicles

This stage contains no AI.

---

## OR-Tools Optimizer

Receives:

* graph
* vehicles
* destinations
* costs
* constraints

Produces:

Optimal fleet routes.

No LLM interaction occurs here.

---

## Validation

Checks that generated routes satisfy:

* vehicle capacity
* weight limits
* height restrictions
* mission deadlines
* operational policies

---

## Monitoring

Continuously monitors:

* new traffic
* accidents
* vehicle failures
* weather

Triggers replanning when required.

---

# Data Sources

Initial implementation:

* OpenStreetMap
* OSMnx
* NetworkX
* Google OR-Tools

Future integrations:

* HERE Traffic API
* TomTom API
* Government road closure feeds
* Internal telemetry
* Vehicle GPS
* Weather APIs
* Bridge databases

All data sources should implement a common interface.

```
class DataSource:

    def fetch(self):
        ...
```

---

# Agent Philosophy

Not everything should be an agent.

Prefer deterministic code whenever possible.

Good use cases for agents:

* mission planning
* explanation generation
* interpreting free-text
* ambiguity resolution
* replanning decisions

Poor use cases:

* API wrappers
* shortest path
* graph algorithms
* deterministic business rules

---

# Future Work

Possible future capabilities:

* Dynamic replanning
* Partial fleet reoptimization
* Multi-objective optimization
* Fuel-aware routing
* CO₂ optimization
* Threat-aware routing
* Predictive traffic modelling
* Simulation using SUMO
* Explainable routing decisions

---

# Core Philosophy

The routing engine should remain mathematically correct and deterministic.

LLMs augment the system by translating human knowledge into structured constraints rather than replacing proven optimization algorithms.

When adding new functionality, ask:

> Can this be implemented deterministically?

If yes, do not use an LLM.

Only introduce AI where genuine reasoning over unstructured information is required.
