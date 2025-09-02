# """Trading strategy engine - generates trading signals."""

# from typing import Optional, Dict, Any
# from common.config import SPREAD_THRESHOLD
# from common.utils import setup_logger, get_timestamp
# import uuid

# logger = setup_logger(__name__)

# class StrategyEngine:
#     def __init__(self):
#         self.name = "SimpleSpreadStrategy"

#     def generate_signal(self, book: Dict[str, Any]) -> Optional[Dict[str, Any]]:
#         """Generate trading signal based on book data."""
#         if not book or "spread" not in book:
#             return None

#         spread = book["spread"]
        
#         # Simple strategy: buy if spread is tight
#         if spread < SPREAD_THRESHOLD:
#             order = {
#                 "order_id": str(uuid.uuid4()),
#                 "symbol": book["symbol"],
#                 "side": "BUY",
#                 "quantity": 100,
#                 "price": book["ask"],
#                 "order_type": "LIMIT",
#                 "timestamp": get_timestamp(),
#                 "strategy": self.name
#             }
            
#             logger.info(
#                 f"Strategy signal: {order['side']} {order['quantity']} "
#                 f"{order['symbol']} @ {order['price']} (spread: {spread})"
#             )
#             return order
        
#         return None


from typing import Optional, Dict, Any
from common.config import SPREAD_THRESHOLD, SPREAD_SELL_THRESHOLD, MAX_POSITION
from common.utils import setup_logger, get_timestamp
import uuid

logger = setup_logger(__name__)

class StrategyEngine:
    def __init__(self):
        self.name = "SimpleSpreadStrategy"

    def generate_signal(self, book: Dict[str, Any], current_positions: Dict[str, int]) -> Optional[Dict[str, Any]]:
        """Generate trading signal based on book data and current positions."""
        logger.info(f"🔍 DEBUG - Raw book: {book}")
        logger.info(f"🔍 DEBUG - Current positions: {current_positions}")
        
        if not book:
            logger.debug("No order book data, skipping signal.")
            return None

        # ✅ FIX: Use dict.get() instead of getattr()
        symbol = book.get("symbol")
        bid = book.get("bid")
        ask = book.get("ask")
        
        logger.info(f"🔍 DEBUG - Extracted: symbol={symbol}, bid={bid}, ask={ask}")
        
        if symbol is None or bid is None or ask is None:
            logger.debug(f"Book missing required data: symbol={symbol}, bid={bid}, ask={ask}")
            return None

        spread = ask - bid
        position = current_positions.get(symbol, 0)

        logger.info(f"🔍 DEBUG - {symbol}: spread={spread:.4f}, position={position}")
        logger.info(f"🔍 DEBUG - Thresholds: BUY<{SPREAD_THRESHOLD}, SELL>{SPREAD_SELL_THRESHOLD}, MAX_POS={MAX_POSITION}")

        # BUY signal: spread tight and position below limit
        if spread < SPREAD_THRESHOLD and position < MAX_POSITION:
            order = {
                "order_id": str(uuid.uuid4()),
                "symbol": symbol,
                "side": "BUY",
                "quantity": min(100, MAX_POSITION - position),
                "price": ask,
                "order_type": "LIMIT",
                "timestamp": get_timestamp(),
                "strategy": self.name
            }
            logger.info(f"🚀 BUY signal generated: {order}")
            return order

        # SELL signal: spread wide and position > 0
        if spread > SPREAD_SELL_THRESHOLD and position > 0:
            order = {
                "order_id": str(uuid.uuid4()),
                "symbol": symbol,
                "side": "SELL",
                "quantity": min(100, position),
                "price": bid,
                "order_type": "LIMIT",
                "timestamp": get_timestamp(),
                "strategy": self.name
            }
            logger.info(f"🚀 SELL signal generated: {order}")
            return order

        logger.debug(f"No signal for {symbol}: spread={spread:.4f}, position={position}")
        return None