from __future__ import annotations

import math
from typing import Any

from shapely.geometry import LineString, Point


class VehicleSimulationService:
    """
    Advances vehicles along their currently assigned routes.

    The simulator is deliberately separate from routing/planning:
      - Planner decides which route a vehicle should take.
      - RouteBuilder constructs the route geometry.
      - This service only advances the vehicle along that route.
      - WorldState remains the source of truth.

    Expected vehicle attributes:
        vehicle_id
        route_id
        current_lat
        current_lon
        route_progress_m
        status

    Expected route structure:
        route.segments

    Expected segment structure:
        segment.geometry -> Shapely LineString
        segment.travel_time_s (optional)
        segment.distance_m (optional)

    Geometry is assumed to be WGS84:
        (longitude, latitude)
    """

    EARTH_RADIUS_M = 6_371_000.0

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
                vehicle=vehicle,
                routes=routes,
                dt_seconds=dt_seconds,
            )

    # ------------------------------------------------------------------
    # Vehicle update
    # ------------------------------------------------------------------

    def _update_vehicle(
            self,
            vehicle: Any,
            routes: Any,
            dt_seconds: float,
    ) -> None:

        route_id = getattr(
            vehicle,
            "current_route_id",
            None,
        )

        print("route_id", route_id)

        if route_id is None:
            return

        route = self._get_route(
            routes,
            route_id,
        )

        if route is None:
            return

        segments = getattr(
            route,
            "segments",
            None,
        )

        if not segments:
            return

        progress = float(
            getattr(
                vehicle,
                "route_progress_m",
                0.0,
            )
            or 0.0
        )

        # Determine how far the vehicle should travel
        # during this simulation tick.
        distance_to_travel = (
                self._vehicle_speed_mps(
                    vehicle=vehicle,
                    route=route,
                    progress_m=progress,
                )
                * dt_seconds
        )

        if distance_to_travel <= 0:
            return

        new_progress = (
                progress
                + distance_to_travel
        )

        route_length = self._route_length(
            segments
        )

        # Route has been completed.
        if (
                route_length > 0
                and new_progress >= route_length
        ):
            new_progress = route_length

            self._set_vehicle_position_at_progress(
                vehicle,
                segments,
                new_progress,
            )

            print(
                f"[SIM] {vehicle.vehicle_id}: "
                f"progress={new_progress:.1f}m "
                f"lat={vehicle.current_lat} "
                f"lon={vehicle.current_lon}"
            )

            self._mark_route_complete(
                vehicle
            )

            return

        self._set_vehicle_position_at_progress(
            vehicle,
            segments,
            new_progress,
        )

        self._set_attribute(
            vehicle,
            "route_progress_m",
            new_progress,
        )

        self._set_attribute(
            vehicle,
            "status",
            "EN_ROUTE",
        )

    # ------------------------------------------------------------------
    # Speed
    # ------------------------------------------------------------------

    def _vehicle_speed_mps(
            self,
            vehicle: Any,
            route: Any,
            progress_m: float,
    ) -> float:
        """
        Determine current vehicle speed.

        Priority:

        1. Segment's current travel time, if available.
        2. Segment's distance / travel time.
        3. Vehicle's configured speed.
        4. A conservative default.

        This allows traffic updates to naturally affect
        simulated vehicle movement.
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
                return (
                        distance
                        / travel_time
                )

        # Try vehicle's configured speed.
        speed = getattr(
            vehicle,
            "speed_mps",
            None,
        )

        if speed is not None:

            try:
                return max(
                    0.0,
                    float(speed),
                )
            except (
                    TypeError,
                    ValueError,
            ):
                pass

        # Try km/h representation.
        speed_kmh = getattr(
            vehicle,
            "speed_kmh",
            None,
        )

        if speed_kmh is not None:

            try:
                return max(
                    0.0,
                    float(speed_kmh)
                    / 3.6,
                    )
            except (
                    TypeError,
                    ValueError,
            ):
                pass

        # Default simulation speed.
        return 10.0

    # ------------------------------------------------------------------
    # Route geometry
    # ------------------------------------------------------------------

    def _set_vehicle_position_at_progress(
            self,
            vehicle: Any,
            segments: list[Any],
            progress_m: float,
    ) -> None:
        """
        Convert route distance into a lat/lon position.
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

        if geometry is None:
            return

        point = self._point_along_linestring(
            geometry,
            local_distance,
        )

        if point is None:
            return

        # Shapely uses:
        #     x = longitude
        #     y = latitude
        #
        # Frontend uses:
        #     [latitude, longitude]

        self._set_attribute(
            vehicle,
            "current_lon",
            float(point.x),
        )

        self._set_attribute(
            vehicle,
            "current_lat",
            float(point.y),
        )

        # Some projects use a tuple position instead.
        if hasattr(vehicle, "position"):
            try:
                self._set_attribute(
                    vehicle,
                    "position",
                    (
                        float(point.y),
                        float(point.x),
                    ),
                )
            except Exception:
                pass

    def _point_along_linestring(
            self,
            geometry: Any,
            distance_m: float,
    ) -> Point | None:
        """
        Return a point approximately `distance_m` metres
        along a WGS84 LineString.

        Shapely's native geometry.length is in degrees when
        using longitude/latitude, so we walk the individual
        coordinate segments using haversine distance.
        """

        if not isinstance(
                geometry,
                LineString,
        ):
            return None

        coordinates = list(
            geometry.coords
        )

        if not coordinates:
            return None

        if len(coordinates) == 1:
            lon, lat = coordinates[0]

            return Point(
                lon,
                lat,
            )

        remaining = max(
            0.0,
            distance_m,
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

                return Point(
                    lon,
                    lat,
                )

            remaining -= segment_distance

        # If progress is past the end, return
        # the final coordinate.
        lon, lat = coordinates[-1]

        return Point(
            lon,
            lat,
        )

    # ------------------------------------------------------------------
    # Segment lookup
    # ------------------------------------------------------------------

    def _find_segment_at_progress(
            self,
            segments: list[Any],
            progress_m: float,
    ) -> tuple[Any | None, float]:
        """
        Find the segment containing a particular
        distance along the route.

        Returns:

            (segment, distance_inside_segment)
        """

        remaining = max(
            0.0,
            progress_m,
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
                    length = self._geometry_length_m(
                        geometry
                    )

            if length is None:
                continue

            if remaining <= length:

                return (
                    segment,
                    remaining,
                )

            remaining -= length

        if segments:

            last = segments[-1]

            length = (
                self._segment_distance(
                    last
                )
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

    # ------------------------------------------------------------------
    # Route length
    # ------------------------------------------------------------------

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

    def _segment_distance(
            self,
            segment: Any,
    ) -> float | None:

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

    def _segment_travel_time(
            self,
            segment: Any,
    ) -> float | None:

        value = getattr(
            segment,
            "travel_time_s",
            None,
        )

        if value is None:
            value = getattr(
                segment,
                "travel_time",
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

    def _geometry_length_m(
            self,
            geometry: LineString,
    ) -> float:

        coordinates = list(
            geometry
        )

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

    # ------------------------------------------------------------------
    # Haversine
    # ------------------------------------------------------------------

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
                math.sin(d_lat / 2) ** 2
                + math.cos(lat1_rad)
                * math.cos(lat2_rad)
                * math.sin(d_lon / 2) ** 2
        )

        c = (
                2
                * math.atan2(
            math.sqrt(a),
            math.sqrt(1 - a),
        )
        )

        return (
                cls.EARTH_RADIUS_M
                * c
        )

    # ------------------------------------------------------------------
    # Completion
    # ------------------------------------------------------------------

    def _mark_route_complete(
            self,
            vehicle: Any,
    ) -> None:

        self._set_attribute(
            vehicle,
            "status",
            "COMPLETED",
        )

        self._set_attribute(
            vehicle,
            "route_progress_m",
            0.0,
        )

        # Keep route_id for now so the frontend can
        # still identify the completed route.
        #
        # If your application expects completed vehicles
        # to become immediately available for another route,
        # change this to:
        #
        # vehicle.route_id = None

    # ------------------------------------------------------------------
    # Route collection helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_routes(
            world: Any,
    ) -> Any:

        return getattr(
            world,
            "routes",
            {},
        )

    @staticmethod
    def _get_route(
            routes: Any,
            route_id: str,
    ) -> Any:

        if isinstance(
                routes,
                dict,
        ):
            return routes.get(
                route_id
            )

        # Support list-based WorldState.routes.
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

    # ------------------------------------------------------------------
    # Safe attribute assignment
    # ------------------------------------------------------------------

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
            # This keeps the simulator from crashing if
            # a particular vehicle model does not expose
            # one of the optional fields.
            pass