import uuid
import logging
from typing import Dict, Any

from common.utils import setup_logger

logger = setup_logger(__name__)

class RiskEngine:
    def __init__(self, position_limit: int = 10000, notional_limit: int = 50000000):
        self.position_limit = position_limit
        self.notional_limit = notional_limit
        self.positions: Dict[str, Dict[str, Any]] = {}  # {symbol: {quantity: int, avg_price: float}}
        self.orders: Dict[str, Dict[str, Any]] = {}     # {order_id: {details}}
        
    def check_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs pre-trade risk checks on a new order.
        Returns a dictionary with a 'status' and 'reason' for rejection if applicable.
        """
        symbol = order.get("symbol")
        quantity = order.get("quantity")
        order_type = order.get("order_type")
        price = order.get("price")
        side = order.get("side")
        order_id = str(uuid.uuid4())
        
        # Add order to internal tracking
        self.orders[order_id] = order
        
        try:
            # Check for required fields
            required_fields = [symbol, quantity, order_type, price, side]
            if any(field is None for field in required_fields):
                logger.warning(f"Order missing required fields: {order}")
                return {**order, "status": "REJECTED", "reason": "MISSING_FIELDS"}

            # Check position limits
            current_position = self.positions.get(symbol, {"quantity": 0})["quantity"]
            if side == "BUY" and current_position + quantity > self.position_limit:
                logger.warning(f"Order {order_id} rejected due to position limit.")
                return {**order, "status": "REJECTED", "reason": "POSITION_LIMIT"}
            
            if side == "SELL" and current_position - quantity < -self.position_limit:
                logger.warning(f"Order {order_id} rejected due to position limit.")
                return {**order, "status": "REJECTED", "reason": "POSITION_LIMIT"}
                
            # Check notional limits (use absolute positions)
            notional_value = quantity * price
            current_notional = sum(abs(pos["quantity"] * pos["avg_price"]) for pos in self.positions.values())
            if current_notional + notional_value > self.notional_limit:
                logger.warning(f"Order {order_id} rejected due to notional limit.")
                return {**order, "status": "REJECTED", "reason": "NOTIONAL_LIMIT"}
            
            logger.info(f"Order passed risk checks: {order_id}")
            return {**order, "order_id": order_id, "status": "APPROVED"}
            
        except Exception as e:
            logger.error(f"Risk check failed for order {order}: {e}")
            return {**order, "status": "REJECTED", "reason": f"INVALID_ORDER: {e}"}

    def apply_fill(self, fill: Dict[str, Any]):
        """
        Updates positions based on a received fill and returns realized PnL for the fill.
        """
        symbol = fill["symbol"]
        filled_quantity = fill["quantity"]
        filled_price = fill["price"]
        side = fill["side"]

        if symbol not in self.positions:
            self.positions[symbol] = {"quantity": 0, "avg_price": 0.0}

        current_pos = self.positions[symbol]["quantity"]
        current_avg_price = self.positions[symbol]["avg_price"]
        realized_pnl = 0.0

        if side == "BUY":
            # If reducing a short position
            if current_pos < 0:
                closed_qty = min(abs(current_pos), filled_quantity)
                realized_pnl = (current_avg_price - filled_price) * closed_qty
            new_quantity = current_pos + filled_quantity
            if new_quantity != 0:
                new_avg_price = (current_pos * current_avg_price + filled_quantity * filled_price) / new_quantity
            else:
                new_avg_price = 0.0
        else:  # SELL
            # If reducing a long position
            if current_pos > 0:
                closed_qty = min(current_pos, filled_quantity)
                realized_pnl = (filled_price - current_avg_price) * closed_qty
            new_quantity = current_pos - filled_quantity
            # For a sell, we assume FIFO accounting; average price stays the same unless flat
            new_avg_price = current_avg_price if new_quantity != 0 else 0.0

        self.positions[symbol]["quantity"] = new_quantity
        self.positions[symbol]["avg_price"] = new_avg_price

        logger.info(
            f"Updated position for {symbol}: quantity={self.positions[symbol]['quantity']}, "
            f"avg_price=${self.positions[symbol]['avg_price']:.2f}, realized_pnl={realized_pnl:.2f}"
        )
        return realized_pnl

    def get_positions(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns the current position data.
        """
        return {symbol: pos for symbol, pos in self.positions.items() if pos["quantity"] != 0}
