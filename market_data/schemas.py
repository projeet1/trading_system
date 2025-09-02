"""Data schemas for market data and orders."""

from dataclasses import dataclass
from typing import Optional

@dataclass
class Tick:
    symbol: str
    bid: float
    ask: float
    bid_size: int
    ask_size: int
    timestamp: float

@dataclass
class Order:
    order_id: str
    symbol: str
    side: str  # "BUY" or "SELL"
    quantity: int
    price: float
    timestamp: float
    status: str = "NEW"

@dataclass
class Fill:
    order_id: str
    symbol: str
    side: str
    quantity: int
    price: float
    timestamp: float