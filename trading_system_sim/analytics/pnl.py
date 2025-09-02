"""PnL calculation engine."""

import sqlite3
from typing import Any, Dict, List
from common.config import DB_PATH
from common.utils import setup_logger

logger = setup_logger(__name__)

class PnLCalculator:
    def __init__(self):
        pass

    def calculate_realized_pnl(self) -> Dict[str, float]:
        """Calculate realized PnL by symbol."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all fills grouped by symbol
        cursor.execute('''
            SELECT symbol, side, quantity, price, timestamp
            FROM fills
            ORDER BY symbol, timestamp
        ''')
        
        fills = cursor.fetchall()
        conn.close()
        
        pnl_by_symbol = {}
        positions = {}  # symbol -> (quantity, avg_price)
        
        for symbol, side, quantity, price, timestamp in fills:
            if symbol not in positions:
                positions[symbol] = [0, 0.0]  # [qty, avg_price]
            
            current_qty, current_avg = positions[symbol]
            
            if side == "BUY":
                # Update position and average price
                new_qty = current_qty + quantity
                new_avg = ((current_qty * current_avg) + (quantity * price)) / new_qty
                positions[symbol] = [new_qty, new_avg]
            else:  # SELL
                if current_qty <= 0:
                    # Nothing to sell, skip or warn
                    continue
                
                # Calculate realized PnL for the amount we can sell
                sell_qty = min(quantity, current_qty)
                realized_pnl = sell_qty * (price - current_avg)
                pnl_by_symbol[symbol] = pnl_by_symbol.get(symbol, 0) + realized_pnl
                
                # Update remaining position
                new_qty = current_qty - sell_qty
                positions[symbol] = [new_qty, current_avg]  # Keep avg_price for remaining shares

        return pnl_by_symbol


    def get_positions_summary(self) -> List[Dict[str, Any]]:
        """Get current positions and unrealized PnL."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, side, SUM(quantity) as total_qty, AVG(price) as avg_price
            FROM fills
            GROUP BY symbol, side
        ''')
        
        fills = cursor.fetchall()
        conn.close()
        
        # Calculate net positions
        positions = {}
        for symbol, side, total_qty, avg_price in fills:
            if symbol not in positions:
                positions[symbol] = {"net_qty": 0, "avg_price": 0, "total_cost": 0}
            
            qty = total_qty if side == "BUY" else -total_qty
            cost = total_qty * avg_price * (1 if side == "BUY" else -1)
            
            positions[symbol]["net_qty"] += qty
            positions[symbol]["total_cost"] += cost
        
        # Calculate average prices
        for symbol in positions:
            if positions[symbol]["net_qty"] != 0:
                positions[symbol]["avg_price"] = abs(
                    positions[symbol]["total_cost"] / positions[symbol]["net_qty"]
                )
        
        return positions