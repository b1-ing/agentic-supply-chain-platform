from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from models.incoming_state import IncomingOrder

from models.order_state import OrderState


SYSTEM_PROMPT = """
You are an expert logistics order extraction system.

Extract a structured delivery order from the user's request.

Infer values where appropriate.

Examples:
- Frozen food -> refrigerated = true
- Chemicals or fuel -> hazardous = true
- Fragile items -> fragile = true

If a value is not provided and cannot be inferred, return null.
Extract the delivery request.

Return EXACTLY one JSON object with these fields:

{{
  "pickup_address": "...",
  "delivery_address": "...",
  "weight_kg": null,
  "volume_m3": null,
  "pallets": null,
  "refrigerated": null,
  "hazardous": null,
  "fragile": null,
  "oversized": null,
  "earliest_pickup": null,
  "latest_pickup": null,
  "earliest_delivery": null,
  "latest_delivery": null,
  "notes": null
}}

Rules:
- Do not wrap inside an "order" object.
- Do not use "origin", "destination", "pickup_location", or "delivery_location".
- Use the field names exactly as above.
- Unknown values must be null.
- Return only JSON.

"""


class OrderExtractionAgent:
    def __init__(self, use_local: bool = True):
        if use_local:
            print("[*] Configuring RoutingAgent to use local model engine...")
            self.llm_engine = ChatOpenAI(
                model="gemini-3.5-flash",  # Matches your local setup
                base_url="http://localhost:8081/v1",
                api_key="sk-your-key",  # Local servers usually require a dummy key
                temperature=0.0,  # Keep it deterministic for structured analysis
            )
        else:
            print("[*] Configuring RoutingAgent to use production OpenAI engine...")
            self.llm_engine = ChatOpenAI(model="gpt-4.1")
        self.llm = self.llm_engine.with_structured_output(IncomingOrder)

        self.prompt = ChatPromptTemplate.from_messages(
            [("system", SYSTEM_PROMPT), ("human", "{order_text}")]
        )

    def extract(self, order_text: str) -> IncomingOrder:

        chain = self.prompt | self.llm

        result = chain.invoke({"order_text": order_text})
        print(type(result))
        print(result)

        if isinstance(result, IncomingOrder):
            return result

        if isinstance(result, dict):
            return IncomingOrder(result)

        raise TypeError(f"Unexpected output type: {type(result)}")
