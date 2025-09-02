"""Market data feed handler - consumes and normalizes ticks."""

import asyncio
import json
import websockets
from typing import Callable, Optional
from common.config import MARKET_DATA_WS_PORT
from common.utils import setup_logger, deserialize_message
from market_data.schemas import Tick

logger = setup_logger(__name__)

class FeedHandler:
    def __init__(self, on_tick_callback: Callable[[Tick], None]):
        self.on_tick_callback = on_tick_callback
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None

    async def connect(self):
        """Connect to market data feed."""
        try:
            self.websocket = await websockets.connect(
                f"ws://localhost:{MARKET_DATA_WS_PORT}"
            )
            logger.info("Connected to market data feed")
        except Exception as e:
            logger.error(f"Failed to connect to feed: {e}")
            raise

    async def listen(self):
        """Listen for incoming market data."""
        if not self.websocket:
            await self.connect()
        
        try:
            async for message in self.websocket:
                tick_data = deserialize_message(message)
                tick = Tick(**tick_data)
                if asyncio.iscoroutinefunction(self.on_tick_callback):
                    await self.on_tick_callback(tick)
                else:
                    self.on_tick_callback(tick)
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection to market data feed lost")
        except Exception as e:
            logger.error(f"Error processing market data: {e}")
            logger.error(f"Tick data: {tick_data if 'tick_data' in locals() else 'N/A'}")

    async def disconnect(self):
        """Disconnect from feed."""
        if self.websocket:
            await self.websocket.close()