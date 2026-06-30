from models.events import TrafficIncident


class ContextBuilder:
    def build(
        self, incidents: list[TrafficIncident], matched_edges: list[list[int]]
    ) -> list[dict]:

        context = []

        for i, (incident, edges) in enumerate(zip(incidents, matched_edges)):
            context.append(
                {
                    "incident_index": i,
                    "type": incident.incident_type,
                    "message": incident.message,
                    "latitude": incident.latitude,
                    "longitude": incident.longitude,
                    "candidate_edges": edges,
                }
            )

        return context
