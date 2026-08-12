# agent/tools/order_tools.py

from services.order.order_service import OrderService

order_service = OrderService()


async def create_order(prompt: str):

    result = await order_service.process_order(prompt)

    return {
        "decision": result["decision"],
        "order_id": result.get("order_id"),
        "world_summary": {
            "new_orders": len(result["world"].new_orders),
            "in_progress": len(result["world"].orders_in_progress),
            "unserviceable": len(result["world"].unserviceable_orders),
        },
    }