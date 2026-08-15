
from __future__ import annotations

import math
from typing import Any

import osmnx as ox


class VehicleSimulationService:
    """
    Advances vehicles along their currently assigned routes.

    Responsibilities
    ----------------
    - Advance vehicles according to simulation time.
    - Move vehicles through route segments.
    - Update vehicle latitude/longitude.
    - Update vehicle.current_node.
    - Track route progress.
    - Track completed route stops.
    - Mark routes as completed.

    Routing/planning is NOT performed here.

    WorldState remains the source of truth.

    Expected Vehicle attributes
    ---------------------------
    vehicle_id
    current_route_id
    current_route
    current_node
    current_lat
    current_lon
    route_progress_m
    completed_stop_sequence
    status

    Expected VehicleRoute attributes
    --------------------------------
    route_id
    vehicle_id
    stops
    segments
    total_distance
    total_travel_time

    Expected RouteSegment attributes
    --------------------------------
    nodes
    geometry
    distance
    travel_time

    Geometry convention
    -------------------
    RouteSegment.geometry uses:

        [(longitude, latitude), ...]

    Frontend routes may serialize this as:

        [[latitude, longitude], ...]

    The simulator always works with the WorldState representation:
        (longitude, latitude)
    """

    EARTH_RADIUS_M = 6_371_000.0

    DEFAULT_SPEED_MPS = 10.0

    # ============================================================
    # PUBLIC API
    # ============================================================

    def update(
        self,
        world: Any,
        dt_seconds: float,
    ) -> None:
        """
        Advance every active vehicle by dt_seconds.
        """

        if dt_seconds <= 0:
            return

        routes = self._get_routes(world)

        for vehicle in getattr(world, "vehicles", []):
            self._update_vehicle(
                world=world,
                vehicle=vehicle,
                routes=routes,
                dt_seconds=dt_seconds,
            )

    # ============================================================
    # VEHICLE UPDATE
    # ============================================================

    def _update_vehicle(
        self,
        world: Any,
        vehicle: Any,
        routes: Any,
        dt_seconds: float,
    ) -> None:

        vehicle_id = getattr(
            vehicle,
            "vehicle_id",
            "UNKNOWN",
        )

        route_id = getattr(
            vehicle,
            "current_route_id",
            None,
        )

        # --------------------------------------------------------
        # Vehicle has no active route.
        # --------------------------------------------------------

        if route_id is None:
            return

        route = self._get_route(
            routes,
            route_id,
        )

        # Compatibility fallback.
        if route is None:
            route = getattr(
                vehicle,
                "current_route",
                None,
            )

        if route is None:
            print(
                f"[SIM] {vehicle_id}: "
                f"route {route_id} not found."
            )
            return

        segments = getattr(
            route,
            "segments",
            None,
        )

        if not segments:
            print(
                f"[SIM] {vehicle_id}: "
                f"route {route_id} has no segments."
            )
            return

        # --------------------------------------------------------
        # Do not move vehicles that are not operationally active.
        # --------------------------------------------------------

        status = str(
            getattr(
                vehicle,
                "status",
                "",
            )
        ).upper()

        if status in {
            "IDLE",
            "AVAILABLE",
            "COMPLETED",
            "CANCELLED",
            "OUT_OF_SERVICE",
        }:
            return

        # --------------------------------------------------------
        # Current route progress.
        # --------------------------------------------------------

        progress = self._safe_float(
            getattr(
                vehicle,
                "route_progress_m",
                0.0,
            ),
            default=0.0,
        )

        # --------------------------------------------------------
        # Determine vehicle speed.
        # --------------------------------------------------------

        speed_mps = self._vehicle_speed_mps(
            vehicle=vehicle,
            route=route,
            progress_m=progress,
        )

        if speed_mps <= 0:
            return

        distance_to_travel = (
            speed_mps * dt_seconds
        )

        if distance_to_travel <= 0:
            return

        # --------------------------------------------------------
        # Determine total route length.
        # --------------------------------------------------------

        route_length = self._route_length(
            segments
        )

        if route_length <= 0:
            print(
                f"[SIM] {vehicle_id}: "
                f"route {route_id} has zero length."
            )
            return

        # --------------------------------------------------------
        # Advance progress.
        # --------------------------------------------------------

        new_progress = (
            progress
            + distance_to_travel
        )

        # ========================================================
        # ROUTE COMPLETE
        # ========================================================

        if new_progress >= route_length:

            new_progress = route_length

            self._set_vehicle_position_at_progress(
                world=world,
                vehicle=vehicle,
                segments=segments,
                progress_m=new_progress,
            )

            self._set_attribute(
                vehicle,
                "route_progress_m",
                new_progress,
            )

            self._update_completed_stops(
                vehicle=vehicle,
                route=route,
                progress_m=new_progress,
            )

            self._mark_route_complete(
                vehicle=vehicle,
                route=route,
            )

            print(
                f"[SIM] {vehicle_id}: "
                f"completed route {route_id}"
            )

            return

        # ========================================================
        # NORMAL MOVEMENT
        # ========================================================

        self._set_vehicle_position_at_progress(
            world=world,
            vehicle=vehicle,
            segments=segments,
            progress_m=new_progress,
        )

        self._set_attribute(
            vehicle,
            "route_progress_m",
            new_progress,
        )

        self._update_completed_stops(
            vehicle=vehicle,
            route=route,
            progress_m=new_progress,
        )

        self._set_attribute(
            vehicle,
            "status",
            "EN_ROUTE",
        )


    # ============================================================
    # SPEED
    # ============================================================

    def _vehicle_speed_mps(
        self,
        vehicle: Any,
        route: Any,
        progress_m: float,
    ) -> float:
        """
        Determine current simulation speed.

        Priority:

        1. Current route segment distance / travel time.
        2. vehicle.speed_mps.
        3. vehicle.speed_kmh.
        4. DEFAULT_SPEED_MPS.
        """

        segments = getattr(
            route,
            "segments",
            [],
        )

        segment, _ = self._find_segment_at_progress(
            segments,
            progress_m,
        )

        if segment is not None:

            distance = self._segment_distance(
                segment
            )

            travel_time = self._segment_travel_time(
                segment
            )

            if (
                distance is not None
                and travel_time is not None
                and travel_time > 0
            ):

                speed = (
                    distance
                    / travel_time
                )

                if speed > 0:
                    return speed

        # --------------------------------------------------------
        # Vehicle speed_mps
        # --------------------------------------------------------

        speed_mps = getattr(
            vehicle,
            "speed_mps",
            None,
        )

        if speed_mps is not None:

            speed = self._safe_float(
                speed_mps,
                default=0.0,
            )

            if speed > 0:
                return speed

        # --------------------------------------------------------
        # Vehicle speed_kmh
        # --------------------------------------------------------

        speed_kmh = getattr(
            vehicle,
            "speed_kmh",
            None,
        )

        if speed_kmh is not None:

            speed = self._safe_float(
                speed_kmh,
                default=0.0,
            )

            if speed > 0:
                return speed / 3.6

        return self.DEFAULT_SPEED_MPS

    # ============================================================
    # POSITION
    # ============================================================

    def _set_vehicle_position_at_progress(
        self,
        world: Any,
        vehicle: Any,
        segments: list[Any],
        progress_m: float,
    ) -> None:
        """
        Convert total route progress into a geographic position.

        Route geometry is represented as:

            [(lon, lat), ...]
        """

        segment, local_distance = (
            self._find_segment_at_progress(
                segments,
                progress_m,
            )
        )

        if segment is None:
            return

        geometry = getattr(
            segment,
            "geometry",
            None,
        )

        if not geometry:
            return

        point = self._point_along_geometry(
            geometry=geometry,
            distance_m=local_distance,
        )

        if point is None:
            return

        lon, lat = point

        # --------------------------------------------------------
        # Update geographic position.
        # --------------------------------------------------------

        self._set_attribute(
            vehicle,
            "current_lon",
            lon,
        )

        self._set_attribute(
            vehicle,
            "current_lat",
            lat,
        )

        # --------------------------------------------------------
        # Optional tuple position.
        #
        # Project convention:
        #     (lat, lon)
        # --------------------------------------------------------

        if hasattr(
            vehicle,
            "position",
        ):

            try:

                self._set_attribute(
                    vehicle,
                    "position",
                    (
                        lat,
                        lon,
                    ),
                )

            except Exception:
                pass

        # --------------------------------------------------------
        # Update graph node.
        #
        # Future rerouting uses current_node as the starting
        # graph node.
        # --------------------------------------------------------

        try:

            nearest_node = ox.distance.nearest_nodes(
                world.graph,
                lon,
                lat,
            )

            self._set_attribute(
                vehicle,
                "current_node",
                nearest_node,
            )

        except Exception as exc:

            print(
                f"[SIM] {getattr(vehicle, 'vehicle_id', 'UNKNOWN')}: "
                f"failed to update current_node: {exc}"
            )

    # ============================================================
    # POINT ALONG GEOMETRY
    # ============================================================

    def _point_along_geometry(
        self,
        geometry: Any,
        distance_m: float,
    ) -> tuple[float, float] | None:
        """
        Return (lon, lat) approximately distance_m metres
        along the route geometry.

        Geometry is expected to be:

            [(lon, lat), ...]

        Haversine distance is used because coordinates are WGS84.
        """

        coordinates = self._normalise_geometry(
            geometry
        )

        if not coordinates:
            return None

        if len(coordinates) == 1:
            return coordinates[0]

        remaining = max(
            0.0,
            float(distance_m),
        )

        for start, end in zip(
            coordinates[:-1],
            coordinates[1:],
        ):

            lon1, lat1 = start
            lon2, lat2 = end

            segment_distance = (
                self._haversine_distance(
                    lat1,
                    lon1,
                    lat2,
                    lon2,
                )
            )

            if segment_distance <= 0:
                continue

            if remaining <= segment_distance:

                ratio = (
                    remaining
                    / segment_distance
                )

                lon = (
                    lon1
                    + (
                        lon2 - lon1
                    )
                    * ratio
                )

                lat = (
                    lat1
                    + (
                        lat2 - lat1
                    )
                    * ratio
                )

                return (
                    lon,
                    lat,
                )

            remaining -= segment_distance

        # --------------------------------------------------------
        # Progress has passed the geometry.
        # Return final coordinate.
        # --------------------------------------------------------

        return coordinates[-1]

    # ============================================================
    # NORMALISE GEOMETRY
    # ============================================================

    @staticmethod
    def _normalise_geometry(
        geometry: Any,
    ) -> list[tuple[float, float]]:
        """
        Convert route geometry into:

            [(lon, lat), ...]

        Your current RouteSegment geometry is expected to already
        be a list of coordinate pairs.

        This method also tolerates tuples and other sequence-like
        coordinate containers.
        """

        if geometry is None:
            return []

        try:
            coordinates = list(geometry)
        except TypeError:
            return []

        result = []

        for coordinate in coordinates:

            if not isinstance(
                coordinate,
                (list, tuple),
            ):
                continue

            if len(coordinate) < 2:
                continue

            try:

                lon = float(
                    coordinate[0]
                )

                lat = float(
                    coordinate[1]
                )

            except (
                TypeError,
                ValueError,
            ):
                continue

            result.append(
                (
                    lon,
                    lat,
                )
            )

        return result

    # ============================================================
    # SEGMENT LOOKUP
    # ============================================================

    def _find_segment_at_progress(
        self,
        segments: list[Any],
        progress_m: float,
    ) -> tuple[Any | None, float]:
        """
        Find the route segment containing total route progress.

        Returns:

            (
                segment,
                distance_inside_segment
            )
        """

        remaining = max(
            0.0,
            float(progress_m),
        )

        for segment in segments:

            length = self._segment_distance(
                segment
            )

            if length is None:

                geometry = getattr(
                    segment,
                    "geometry",
                    None,
                )

                if geometry is not None:
                    length = (
                        self._geometry_length_m(
                            geometry
                        )
                    )

            if length is None:
                continue

            if remaining <= length:

                return (
                    segment,
                    remaining,
                )

            remaining -= length

        # --------------------------------------------------------
        # Progress is beyond route end.
        # --------------------------------------------------------

        if segments:

            last = segments[-1]

            length = self._segment_distance(
                last
            )

            if length is None:

                geometry = getattr(
                    last,
                    "geometry",
                    None,
                )

                if geometry is not None:
                    length = (
                        self._geometry_length_m(
                            geometry
                        )
                    )

            return (
                last,
                length or 0.0,
            )

        return (
            None,
            0.0,
        )

    # ============================================================
    # ROUTE LENGTH
    # ============================================================

    def _route_length(
        self,
        segments: list[Any],
    ) -> float:

        total = 0.0

        for segment in segments:

            distance = self._segment_distance(
                segment
            )

            if distance is None:

                geometry = getattr(
                    segment,
                    "geometry",
                    None,
                )

                if geometry is not None:

                    distance = (
                        self._geometry_length_m(
                            geometry
                        )
                    )

            if distance is not None:
                total += distance

        return total

    # ============================================================
    # SEGMENT DISTANCE
    # ============================================================

    @staticmethod
    def _segment_distance(
        segment: Any,
    ) -> float | None:
        """
        Support the distance field names currently used
        throughout the routing code.
        """

        value = getattr(
            segment,
            "distance",
            None,
        )

        if value is None:
            value = getattr(
                segment,
                "distance_m",
                None,
            )

        if value is None:
            value = getattr(
                segment,
                "length_m",
                None,
            )

        if value is None:
            return None

        try:

            return max(
                0.0,
                float(value),
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    # ============================================================
    # SEGMENT TRAVEL TIME
    # ============================================================

    @staticmethod
    def _segment_travel_time(
        segment: Any,
    ) -> float | None:
        """
        Support the travel-time field names currently used
        throughout the routing code.
        """

        value = getattr(
            segment,
            "travel_time",
            None,
        )

        if value is None:
            value = getattr(
                segment,
                "travel_time_s",
                None,
            )

        if value is None:
            return None

        try:

            return max(
                0.0,
                float(value),
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    # ============================================================
    # GEOMETRY LENGTH
    # ============================================================

    def _geometry_length_m(
        self,
        geometry: Any,
    ) -> float:
        """
        Calculate WGS84 route geometry length in metres.
        """

        coordinates = self._normalise_geometry(
            geometry
        )

        if len(coordinates) < 2:
            return 0.0

        total = 0.0

        for start, end in zip(
            coordinates[:-1],
            coordinates[1:],
        ):

            lon1, lat1 = start
            lon2, lat2 = end

            total += (
                self._haversine_distance(
                    lat1,
                    lon1,
                    lat2,
                    lon2,
                )
            )

        return total

    # ============================================================
    # STOP TRACKING
    # ============================================================

    def _update_completed_stops(
        self,
        vehicle: Any,
        route: Any,
        progress_m: float,
    ) -> None:
        """
        Mark stops as completed based on cumulative route distance.

        Your current routing architecture creates one route segment
        between each pair of consecutive stops:

            stop 0 -> segment 0 -> stop 1
            stop 1 -> segment 1 -> stop 2
            stop 2 -> segment 2 -> stop 3
        """

        stops = getattr(
            route,
            "stops",
            [],
        )

        segments = getattr(
            route,
            "segments",
            [],
        )

        if not stops:
            return

        completed_sequence = self._safe_int(
            getattr(
                vehicle,
                "completed_stop_sequence",
                -1,
            ),
            default=-1,
        )

        cumulative_distance = 0.0

        for index, stop in enumerate(stops):

            # First stop is the vehicle's starting position.
            if index == 0:
                continue

            segment_index = index - 1

            if segment_index >= len(segments):
                break

            segment = segments[
                segment_index
            ]

            length = self._segment_distance(
                segment
            )

            if length is None:

                geometry = getattr(
                    segment,
                    "geometry",
                    None,
                )

                if geometry is not None:

                    length = (
                        self._geometry_length_m(
                            geometry
                        )
                    )

            if length is None:
                continue

            cumulative_distance += length

            sequence = self._safe_int(
                getattr(
                    stop,
                    "sequence",
                    index,
                ),
                default=index,
            )

            if (
                progress_m >= cumulative_distance
                and sequence > completed_sequence
            ):

                completed_sequence = sequence

                vehicle_id = getattr(
                    vehicle,
                    "vehicle_id",
                    "UNKNOWN",
                )

                kind = getattr(
                    stop.location,
                    "kind",
                    "unknown",
                ) if getattr(
                    stop,
                    "location",
                    None,
                ) is not None else "unknown"

                print(
                    f"[SIM] {vehicle_id}: "
                    f"reached stop {sequence} "
                    f"({kind})"
                )

        self._set_attribute(
            vehicle,
            "completed_stop_sequence",
            completed_sequence,
        )

    # ============================================================
    # ROUTE COMPLETION
    # ============================================================

    def _mark_route_complete(
        self,
        vehicle: Any,
        route: Any,
    ) -> None:
        """
        Mark vehicle as available after completing its route.

        The completed route remains in world.routes so that the
        frontend can still display route history.

        current_route_id is cleared because it represents the
        vehicle's ACTIVE route.
        """

        stops = getattr(
            route,
            "stops",
            [],
        )

        if stops:

            final_sequence = max(
                (
                    self._safe_int(
                        getattr(
                            stop,
                            "sequence",
                            -1,
                        ),
                        default=-1,
                    )
                    for stop in stops
                ),
                default=-1,
            )

            self._set_attribute(
                vehicle,
                "completed_stop_sequence",
                final_sequence,
            )

        # Preserve the completed route separately if the vehicle
        # model supports this field.
        current_route_id = getattr(
            vehicle,
            "current_route_id",
            None,
        )

        if current_route_id is not None:

            self._set_attribute(
                vehicle,
                "last_completed_route_id",
                current_route_id,
            )

        self._set_attribute(
            vehicle,
            "route_progress_m",
            0.0,
        )

        self._set_attribute(
            vehicle,
            "status",
            "AVAILABLE",
        )

        self._set_attribute(
            vehicle,
            "current_route_id",
            None,
        )

        self._set_attribute(
            vehicle,
            "current_route",
            None,
        )

    # ============================================================
    # ROUTE COLLECTION
    # ============================================================

    @staticmethod
    def _get_routes(
        world: Any,
    ) -> Any:

        return getattr(
            world,
            "routes",
            [],
        )

    @staticmethod
    def _get_route(
        routes: Any,
        route_id: str,
    ) -> Any:

        # --------------------------------------------------------
        # Dictionary-based WorldState.routes
        # --------------------------------------------------------

        if isinstance(
            routes,
            dict,
        ):

            return routes.get(
                route_id
            )

        # --------------------------------------------------------
        # List-based WorldState.routes
        # --------------------------------------------------------

        if isinstance(
            routes,
            (list, tuple),
        ):

            for route in routes:

                if getattr(
                    route,
                    "route_id",
                    None,
                ) == route_id:

                    return route

        return None

    # ============================================================
    # HAVERSINE
    # ============================================================

    @classmethod
    def _haversine_distance(
        cls,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:

        lat1_rad = math.radians(
            lat1
        )

        lat2_rad = math.radians(
            lat2
        )

        d_lat = math.radians(
            lat2 - lat1
        )

        d_lon = math.radians(
            lon2 - lon1
        )

        a = (
            math.sin(
                d_lat / 2
            ) ** 2
            +
            math.cos(lat1_rad)
            * math.cos(lat2_rad)
            * math.sin(
                d_lon / 2
            ) ** 2
        )

        # Protect against floating-point drift.
        a = min(
            1.0,
            max(
                0.0,
                a,
            ),
        )

        c = (
            2
            * math.atan2(
                math.sqrt(a),
                math.sqrt(1.0 - a),
            )
        )

        return (
            cls.EARTH_RADIUS_M
            * c
        )

    # ============================================================
    # SAFE CONVERSION HELPERS
    # ============================================================

    @staticmethod
    def _safe_float(
        value: Any,
        default: float = 0.0,
    ) -> float:

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):

            return default

    @staticmethod
    def _safe_int(
        value: Any,
        default: int = 0,
    ) -> int:

        try:
            return int(value)

        except (
            TypeError,
            ValueError,
        ):

            return default

    # ============================================================
    # SAFE ATTRIBUTE SETTER
    # ============================================================

    @staticmethod
    def _set_attribute(
        obj: Any,
        name: str,
        value: Any,
    ) -> None:

        try:

            setattr(
                obj,
                name,
                value,
            )

        except (
            AttributeError,
            TypeError,
        ):

            pass

