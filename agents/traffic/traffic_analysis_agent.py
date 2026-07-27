from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from models.traffic.traffic_analysis import TrafficAnalysis
from models.traffic.traffic_incident import TrafficIncident


SYSTEM_PROMPT = """
You are an expert traffic operations analyst.

Your job is to analyse one traffic incident and determine how severe it is
for a logistics routing system.

You are NOT responsible for routing vehicles.

You are NOT responsible for modifying the road graph.

For each incident determine:

- severity (0.0 - 1.0)
- whether the incident should affect routing
- estimated duration (minutes)
- recommended penalty type
- recommended radius of influence (metres)
- recommended maximum additional delay (seconds)
- confidence
- reasoning

Guidelines

Minor congestion
- Low severity
- Small radius
- Small delay

Major accident
- High severity
- Large radius
- Large delay

Road closure
- Very high severity
- No delay
- Recommend closure

Roadworks
- Medium severity

Flood
- High severity
- Radius depending on extent

Return ONLY the structured object.
"""


class TrafficAnalysisAgent:
    def __init__(self, use_local: bool = True):

        if use_local:
            self.llm_engine = ChatOpenAI(
                model="gemini-3.5-flash",
                base_url="http://localhost:8081/v1",
                api_key="sk-your-key",
                temperature=0.0,
            )

        else:
            self.llm_engine = ChatOpenAI(
                model="gpt-4.1",
                temperature=0.0,
            )

        self.llm = self.llm_engine.with_structured_output(TrafficAnalysis)

        self.prompt = ChatPromptTemplate.from_messages(
            [("system", SYSTEM_PROMPT), ("human", "{incident}")]
        )

    async def analyse(
        self,
        incident: TrafficIncident,
    ) -> TrafficAnalysis:

        chain = self.prompt | self.llm

        return await chain.ainvoke(
            {
                "incident": self._summarise_incident(
                    incident,
                )
            }
        )

    def _summarise_incident(
        self,
        incident: TrafficIncident,
    ):

        return {
            "id": incident.incident_id,
            "type": incident.incident_type,
            "description": incident.description,
            "road": incident.road_name,
            "latitude": incident.latitude,
            "longitude": incident.longitude,
            "source": incident.source,
            "severity": incident.severity,
        }
