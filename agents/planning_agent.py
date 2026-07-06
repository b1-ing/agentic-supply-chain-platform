from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from models.assessment import PlanningResult

SYSTEM_PROMPT = """
You are an operations planning assistant for a fleet routing system.
Your job is NOT to compute routes.

You will receive a list of traffic incidents that have already been matched to the road network.
You must return a single valid JSON object matching the schema layout below.

For EACH incident inside the context, you must append an assessment object to the "assessments" list.

CRITICAL: Your output must strictly follow this JSON structure:
{{
  "assessments": [
    {{
      "incident_index": 0,
      "severity": "LOW",
      "road_status": "PARTIAL",
      "expected_delay_minutes": 5,
      "affects_routing": false,
      "reason": "Short distinct explanation for incident 0"
    }}
  ],
  "recommend_replan": true,
  "summary": "Global overview summarizing why the fleet should or should not be replanned."
}}

Rules for values:
- "severity" must be exactly one of: LOW, MEDIUM, HIGH, CRITICAL
- "road_status" must be exactly one of: OPEN, PARTIAL, CLOSED
- "incident_index" must match the index of the evaluated raw context item.

CRITICAL: Return ONLY raw, valid JSON. Do not write any markdown code fences like ```json or trailing text.
"""


class PlanningAgent:
    def __init__(self, use_local: bool = True):
        # 1. Check if we want to point to the local server
        if use_local:
            print("[*] Configuring PlanningAgent to use local model engine...")
            self.llm_engine = ChatOpenAI(
                model="gemini-3.5-flash-thinking",  # Matches your local setup
                base_url="http://localhost:8081/v1",
                api_key="sk-your-key",  # Local servers usually require a dummy key
                temperature=0.0,  # Keep it deterministic for structured analysis
            )
        else:
            print("[*] Configuring PlanningAgent to use production OpenAI engine...")
            self.llm_engine = ChatOpenAI(model="gpt-4.1")

        # 2. Attach your structured Pydantic model output schema
        # NOTE: See the crucial tip below regarding local structured outputs
        self.llm = self.llm_engine.with_structured_output(
            PlanningResult,
            method="json_mode",  # Recommended fallback for local open-source model servers
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [("system", SYSTEM_PROMPT), ("human", "{context}")]
        )

    def evaluate(self, context: str) -> PlanningResult:
        chain = self.prompt | self.llm
        return chain.invoke({"context": context})
