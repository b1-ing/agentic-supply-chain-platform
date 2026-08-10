from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from models.order.incoming_order import IncomingOrder

from models.order.order_state import OrderState


SYSTEM_PROMPT = """You are an expert logistics order extraction system.

Your task is to extract a **single structured logistics order** from the user's request.

Return **exactly one JSON object** matching the schema below.

## General Rules

* Return **ONLY** valid raw JSON.
* Do **NOT** wrap the result inside another object.
* Do **NOT** include markdown, explanations, or code fences.
* Use the field names exactly as specified.
* Unknown values must be `null`.
* Do not invent values that cannot reasonably be inferred.

## Address Rules

Extract:

* `pickup_address`
* `delivery_address`

Use the addresses exactly as written by the user whenever possible.

Do NOT use alternative field names such as:

* origin
* destination
* pickup_location
* delivery_location

## Shipment Attribute Rules

You are expected to infer transport constraints using common logistics knowledge.

Do not wait for the user to explicitly mention refrigeration, hazardous materials,
fragility, or oversized transport if these are obvious from the cargo.

### Weight

Examples:

* "500kg" → `500`
* "2 tonnes" → `2000`

Store in kilograms.

### Height

Extract the physical shipment height.

Examples:

* "20m tall item" → `20.0`
* "3.5 metre crate" → `3.5`
* "6-meter equipment" → `6.0`

Store in metres.

### Volume

Examples:

* "12 cubic metres"
* "4 m3"

Store in cubic metres.

### Pallets

Extract the number of pallets.

Examples:

* "8 pallets"
* "24 pallets"

### Refrigerated

Set to `true` if the shipment requires temperature-controlled transport.

Examples:

* frozen food
* chilled food
* seafood
* vaccines
* dairy

Otherwise use `false` if explicitly stated, or `null` if unknown.

### Hazardous

Set to `true` for dangerous goods.

Examples:

* chemicals
* fuel
* LPG
* flammable liquids
* corrosives
* toxic materials

### Fragile

Set to `true` for fragile cargo.

Examples:

* glass
* artwork
* electronics
* MRI scanner
* laboratory equipment

### Oversized

Set to `true` if the shipment exceeds normal transport dimensions.

Examples:

* oversized cargo
* abnormal load
* crane
* excavator
* 20m tall object
* extra-wide equipment

**Oversized does NOT replace height.**

For example:

"Transport a 20m tall object"

should produce

* `"height_m": 20.0`
* `"oversized": true`

### Time Windows

Extract:

* earliest_pickup
* latest_pickup
* earliest_delivery
* latest_delivery

Preserve the user's intended time whenever possible.

If no time is given, return `null`.

### Notes

Store any useful operational information that is not represented elsewhere.

Examples:

* "Live animal transport"
* "Handle upright"
* "Do not stack"
* "Escort vehicle required"

## Output Schema


"pickup_address": "...",
"delivery_address": "...",
"height_m": null,
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


"""


class OrderExtractionAgent:
    def __init__(self, use_local: bool = True):
        if use_local:
            print("[*] Configuring RoutingAgent to use local model engine...")
            self.llm_engine = ChatOpenAI(
                model="gemma3:4b",  # Matches your local setup
                base_url="http://localhost:11434/v1",
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
