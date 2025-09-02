"""Market data feed generator - simulates real market data."""

import asyncio
import json
import random
import websockets
from common.config import SYMBOLS, TICK_INTERVAL, MARKET_DATA_WS_PORT
from common.utils import setup_logger, get_timestamp

logger = setup_logger(__name__)

class MarketDataFeed:
    def __init__(self):
        self.prices = {symbol: random.uniform(100, 300) for symbol in SYMBOLS}
        self.clients = set()

    async def generate_tick(self, symbol: str) -> dict:
        """Generate a realistic market tick."""
        # Random walk with mean reversion
        current_price = self.prices[symbol]
        change = random.uniform(-0.5, 0.5)
        self.prices[symbol] = max(1.0, current_price + change)
        
        bid = self.prices[symbol] - random.uniform(0.01, 0.05)
        ask = bid + random.uniform(0.01, 0.10)
        
        return {
            "symbol": symbol,
            "bid": round(bid, 2),
            "ask": round(ask, 2),
            "bid_size": random.randint(100, 1000),
            "ask_size": random.randint(100, 1000),
            "timestamp": get_timestamp()
        }

    async def broadcast_tick(self, tick: dict):
        """Broadcast tick to all connected clients."""
        if self.clients:
            message = json.dumps(tick)
            disconnected = set()
            for client in self.clients:
                try:
                    await client.send(message)
                except websockets.exceptions.ConnectionClosed:
                    disconnected.add(client)
            
            # Clean up disconnected clients
            self.clients -= disconnected

    async def handle_client(self, websocket, path):
        """Handle new client connection."""
        self.clients.add(websocket)
        logger.info(f"New client connected. Total: {len(self.clients)}")
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            logger.info(f"Client disconnected. Total: {len(self.clients)}")

    async def run_feed(self):
        """Main feed generation loop."""
        while True:
            symbol = random.choice(SYMBOLS)
            tick = await self.generate_tick(symbol)
            await self.broadcast_tick(tick)
            await asyncio.sleep(TICK_INTERVAL)

    async def start_server(self):
        """Start the WebSocket server."""
        logger.info(f"Starting market data feed on port {MARKET_DATA_WS_PORT}")
        
        # Start WebSocket server
        start_server = websockets.serve(
            self.handle_client, 
            "localhost", 
            MARKET_DATA_WS_PORT
        )
        
        # Run feed and server concurrently
        await asyncio.gather(
            start_server,
            self.run_feed()
        )

async def main():
    feed = MarketDataFeed()
    await feed.start_server()

if __name__ == "__main__":
    asyncio.run(main())