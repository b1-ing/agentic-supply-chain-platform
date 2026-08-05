from pathlib import Path

import folium

from models.routing.route_plan import RoutePlan
from folium.plugins import PolyLineTextPath

class RouteVisualiser:
    """
    Visualises a RoutePlan on an interactive Folium map.
    """

    _COLOURS = [
        "blue",
        "red",
        "green",
        "purple",
        "orange",
        "darkred",
        "cadetblue",
        "darkgreen",
        "black",
    ]

    def save(
        self,
        route_plan: RoutePlan,
        output_file: str = "output/routes.html",
    ):

        centre = self._find_centre(route_plan)

        m = folium.Map(
            location=centre,
            zoom_start=12,
            control_scale=True,
        )

        ###############################################################
        # Draw routes
        ###############################################################

        for index, route in enumerate(route_plan.routes):

            colour = self._COLOURS[index % len(self._COLOURS)]

            #
            # Draw road geometry
            #
            for segment in route.segments:

                if not segment.geometry:
                    continue

                line = folium.PolyLine(
                    locations=segment.geometry,
                    color=colour,
                    weight=5,
                    opacity=0.8,
                    tooltip=route.vehicle_id,
                ).add_to(m)
                # --- Add Direction A   rrows ---
                PolyLineTextPath(
                    line,
                    " ► ",               # Arrow character (or '►', '➜', '>>')
                    repeat=True,          # Repeat along the segment length
                    offset=6,             # Vertical offset from the polyline
                    attributes={"fill": colour, "font-size": "14px", "font-weight": "bold"},
                ).add_to(m)
            #
            # Draw stops
            #
            for stop in route.stops:

                location = stop.location

                popup = (
                    f"<b>{location.kind.title()}</b><br>"
                    f"Vehicle: {route.vehicle_id}<br>"
                    f"Order: {location.order_id or '-'}"
                )

                if location.kind == "start":

                    icon = folium.Icon(
                        color="black",
                        icon="play",
                        prefix="fa",
                    )

                elif location.kind == "end":

                    icon = folium.Icon(
                        color="black",
                        icon="stop",
                        prefix="fa",
                    )

                elif location.kind == "pickup":

                    icon = folium.Icon(
                        color="green",
                        icon="arrow-up",
                        prefix="fa",
                    )

                elif location.kind == "delivery":

                    icon = folium.Icon(
                        color="red",
                        icon="arrow-down",
                        prefix="fa",
                    )

                else:

                    icon = folium.Icon(color="blue")

                folium.Marker(
                    location=[location.lat, location.lon],
                    popup=popup,
                    tooltip=location.kind.title(),
                    icon=icon,
                ).add_to(m)

        ###############################################################
        # Save
        ###############################################################

        output = Path(output_file)
        output.parent.mkdir(parents=True, exist_ok=True)

        m.save(str(output))

        print(f"Saved map to {output.resolve()}")

    ####################################################################
    # Helpers
    ####################################################################

    def _find_centre(
        self,
        route_plan: RoutePlan,
    ) -> tuple[float, float]:

        for route in route_plan.routes:

            for stop in route.stops:

                if (
                    stop.location.lat is not None
                    and stop.location.lon is not None
                ):
                    return (
                        stop.location.lat,
                        stop.location.lon,
                    )

        return (
            1.3521,
            103.8198,
        )