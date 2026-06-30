from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from models.assessment import PlanningResult

SYSTEM_PROMPT = """
You are an operations planner.
You are NOT solving routes.

For each incident determine:
- severity
- road status
- estimated delay
- whether it affects routing

Finally decide whether the fleet should be replanned.

CRITICAL: Return a FLAT JSON object only. Do NOT nest fields inside categories like 'incident' or 'decision'.

Your JSON response must look exactly like this structure:
{{
    "severity": "string",
    "road_status": "string",
    "estimated_delay": "string",
    "affects_routing": true/false,
    "recommend_replan": true/false
}}
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
