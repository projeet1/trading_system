"""Common utilities for the trading system."""

import time
import json
import logging
from datetime import datetime
from typing import Any, Dict

def setup_logger(name: str) -> logging.Logger:
    """Set up a logger with consistent formatting."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def get_timestamp() -> float:
    """Get high-precision timestamp."""
    return time.time()

def serialize_message(data: Dict[str, Any]) -> str:
    """Serialize message to JSON."""
    return json.dumps(data, default=str)

def deserialize_message(msg: str) -> Dict[str, Any]:
    """Deserialize JSON message."""
    return json.loads(msg)