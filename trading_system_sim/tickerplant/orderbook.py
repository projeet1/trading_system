"""Order book implementation - maintains best bid/offer."""

from typing import Dict, Optional
from market_data.schemas import Tick
from common.utils import setup_logger

logger = setup_logger(__name__)

class OrderBook:
    def __init__(self):
        self.books: Dict[str, Dict[str, float]] = {}

    def update(self, tick: Tick) -> Dict[str, float]:
        """Update order book with new tick."""
        book_data = {
            "symbol": tick.symbol,
            "bid": tick.bid,
            "ask": tick.ask,
            "bid_size": tick.bid_size,
            "ask_size": tick.ask_size,
            "spread": round(tick.ask - tick.bid, 4),
            "mid": round((tick.bid + tick.ask) / 2, 4),
            "timestamp": tick.timestamp
        }
        
        self.books[tick.symbol] = book_data
        logger.debug(f"Updated {tick.symbol}: {book_data}")
        return book_data

    def get_book(self, symbol: str) -> Optional[Dict[str, float]]:
        """Get current book for symbol."""
        return self.books.get(symbol)

    def get_all_books(self) -> Dict[str, Dict[str, float]]:
        """Get all current books."""
        return self.books.copy()