"""Order Management Service - handles order lifecycle."""

import sqlite3
from typing import Dict, Any, List
from common.config import DB_PATH
from common.utils import setup_logger, get_timestamp

logger = setup_logger(__name__)

class OrderManagementService:
    def __init__(self):
        self.init_db()
        self.orders = {}  # order_id -> order

    def init_db(self):
        """Initialize SQLite database for order history."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                symbol TEXT,
                side TEXT,
                quantity INTEGER,
                price REAL,
                timestamp REAL,
                status TEXT,
                strategy TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fills (
                fill_id TEXT PRIMARY KEY,
                order_id TEXT,
                symbol TEXT,
                side TEXT,
                quantity INTEGER,
                price REAL,
                timestamp REAL
            )
        ''')
        
        conn.commit()
        conn.close()

    def submit_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Submit order to OMS."""
        order_id = order["order_id"]
        self.orders[order_id] = order
        
        # Log to database
        self._save_order_to_db(order)
        
        logger.info(f"Order submitted: {order_id}")
        return order

    def update_order_status(self, order_id: str, status: str, reason: str = None):
        """Update order status."""
        if order_id in self.orders:
            self.orders[order_id]["status"] = status
            if reason:
                self.orders[order_id]["reason"] = reason
            
            # Update database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE orders SET status = ? WHERE order_id = ?",
                (status, order_id)
            )
            conn.commit()
            conn.close()

    def record_fill(self, fill: Dict[str, Any]):
        """Record a fill."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO fills (fill_id, order_id, symbol, side, quantity, price, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            fill.get("fill_id", fill["order_id"] + "_fill"),
            fill["order_id"],
            fill["symbol"], 
            fill["side"],
            fill["quantity"],
            fill["price"],
            fill["timestamp"]
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Fill recorded: {fill}")

    def _save_order_to_db(self, order: Dict[str, Any]):
        """Save order to database."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO orders 
            (order_id, symbol, side, quantity, price, timestamp, status, strategy)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order["order_id"],
            order["symbol"],
            order["side"],
            order["quantity"],
            order["price"],
            order["timestamp"],
            order["status"],
            order.get("strategy", "")
        ))
        
        conn.commit()
        conn.close()

    def get_orders(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent orders in dashboard format."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT timestamp, symbol, side, quantity, price, status, strategy, order_id
            FROM orders 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        orders = []
        for row in cursor.fetchall():
            timestamp, symbol, side, quantity, price, status, strategy, order_id = row
            orders.append({
                'timestamp': timestamp,
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'status': status,
                'strategy': strategy,
                'order_id': order_id
            })
        conn.close()
        return orders