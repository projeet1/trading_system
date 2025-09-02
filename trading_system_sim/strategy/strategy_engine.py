"""Trading strategy engine - generates trading signals."""

from typing import Optional, Dict, Any
from common.config import SPREAD_THRESHOLD
from common.utils import setup_logger, get_timestamp
import uuid

logger = setup_logger(__name__)

class StrategyEngine:
    def __init__(self):
        self.name = "SimpleSpreadStrategy"

    def generate_signal(self, book: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate trading signal based on book data."""
        if not book or "spread" not in book:
            return None

        spread = book["spread"]
        
        # Simple strategy: buy if spread is tight
        if spread < SPREAD_THRESHOLD:
            order = {
                "order_id": str(uuid.uuid4()),
                "symbol": book["symbol"],
                "side": "BUY",
                "quantity": 100,
                "price": book["ask"],
                "order_type": "LIMIT",
                "timestamp": get_timestamp(),
                "strategy": self.name
            }
            
            logger.info(
                f"Strategy signal: {order['side']} {order['quantity']} "
                f"{order['symbol']} @ {order['price']} (spread: {spread})"
            )
            return order
        
        return None

# strategy_engine.py
# from typing import Optional, Dict, Any
# from common.config import SPREAD_THRESHOLD, SPREAD_SELL_THRESHOLD, MAX_POSITION
# from common.utils import setup_logger, get_timestamp
# import uuid

# logger = setup_logger(__name__)

# class StrategyEngine:
#     def __init__(self):
#         self.name = "SpreadStrategy"

#     def generate_signal(
#         self, 
#         book: Dict[str, Any], 
#         current_positions: Dict[str, Any]
#     ) -> Optional[Dict[str, Any]]:
#         """
#         Generate a trading signal (BUY or SELL) based on the market book
#         and current positions.
#         """
#         if not book or "spread" not in book:
#             return None

#         symbol = book["symbol"]
#         spread = book["spread"]
#         current_qty = current_positions.get(symbol, {}).get("net_qty", 0)

#         # Buy signal: tight spread and below max position
#         if spread < SPREAD_THRESHOLD and current_qty < MAX_POSITION:
#             order = {
#                 "order_id": str(uuid.uuid4()),
#                 "symbol": symbol,
#                 "side": "BUY",
#                 "quantity": min(100, MAX_POSITION - current_qty),
#                 "price": book["ask"],
#                 "order_type": "LIMIT",
#                 "timestamp": get_timestamp(),
#                 "strategy": self.name
#             }
#             logger.info(f"BUY signal: {order}")
#             return order

#         # Sell signal: wide spread and we have position to sell
#         if spread > SPREAD_SELL_THRESHOLD and current_qty > 0:
#             order = {
#                 "order_id": str(uuid.uuid4()),
#                 "symbol": symbol,
#                 "side": "SELL",
#                 "quantity": current_qty,  # sell entire position
#                 "price": book["bid"],
#                 "order_type": "LIMIT",
#                 "timestamp": get_timestamp(),
#                 "strategy": self.name
#             }
#             logger.info(f"SELL signal: {order}")
#             return order

#         return None
