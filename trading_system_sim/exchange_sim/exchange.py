"""Exchange simulator - simulates order matching and fills."""

import random
import uuid
import asyncio
from typing import Dict, Any
from common.utils import setup_logger, get_timestamp

logger = setup_logger(__name__)

class ExchangeSimulator:
    def __init__(self):
        self.fill_rate = 0.85  # 85% of orders get filled
        self.latency_ms = (1, 50)  # simulated latency range

    async def process_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Process order and return fill or rejection."""
        try:
            # Validate required fields
            required = {"order_id", "symbol", "side", "quantity", "price"}
            if not required.issubset(order):
                missing = required - set(order.keys())
                logger.error(f"Invalid order, missing fields: {missing}")
                return {
                    "status": "REJECTED",
                    "reason": f"INVALID_ORDER: missing {missing}",
                    "timestamp": get_timestamp()
                }

            # Simulate network latency
            latency = random.uniform(*self.latency_ms) / 1000
            await asyncio.sleep(latency)

            # Simulate fill probability
            if random.random() < self.fill_rate:
                # Simulate partial fills occasionally
                fill_quantity = order["quantity"]
                if random.random() < 0.1:  # 10% chance of partial fill
                    fill_quantity = random.randint(1, order["quantity"])

                # Add some slippage
                slippage = random.uniform(-0.02, 0.02)
                fill_price = order["price"] + slippage

                fill = {
                    "fill_id": str(uuid.uuid4()),
                    "order_id": order["order_id"],
                    "symbol": order["symbol"],
                    "side": order["side"],
                    "quantity": fill_quantity,
                    "price": round(fill_price, 2),
                    "timestamp": get_timestamp(),
                    "status": "FILLED"
                }

                logger.info(
                    f"FILLED: {fill['quantity']} {fill['symbol']} @ {fill['price']} "
                    f"(slippage: {slippage:.4f})"
                )
                return fill
            else:
                # Rejection
                rejection = {
                    **order,
                    "status": "REJECTED",
                    "reason": "MARKET_REJECT",
                    "timestamp": get_timestamp()
                }
                logger.info(f"REJECTED: {order['order_id']} - {rejection['reason']}")
                return rejection

        except Exception as e:
            logger.error(f"Exchange error: {e}", exc_info=True)
            return {
                "status": "REJECTED",
                "reason": "EXCHANGE_ERROR",
                "timestamp": get_timestamp()
            }
