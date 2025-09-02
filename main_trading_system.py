import asyncio
import time
from typing import Dict, Any

from market_data.feed_handler import FeedHandler
from tickerplant.orderbook import OrderBook
from strategy.strategy_engine import StrategyEngine
from risk.risk_engine import RiskEngine
from oms.oms import OrderManagementService
from exchange_sim.exchange import ExchangeSimulator
from analytics.pnl import PnLCalculator
from analytics.dashboard import broadcast_update
from common.utils import setup_logger

logger = setup_logger(__name__)

class TradingSystem:
    def __init__(self):
        self.orderbook = OrderBook()
        self.strategy = StrategyEngine()
        self.risk = RiskEngine()
        self.oms = OrderManagementService()
        self.exchange = ExchangeSimulator()
        self.pnl_calc = PnLCalculator()
        
        # Setup feed handler with callback
        self.feed_handler = FeedHandler(self.on_tick)
        
        # Stats
        self.stats = {
            "ticks_processed": 0,
            "signals_generated": 0,
            "orders_sent": 0,
            "fills_received": 0
        }

    async def on_tick(self, tick):
        """Process incoming market tick."""
        try:
            logger.info(f"Received tick: {tick}")

            # Update order book
            book = self.orderbook.update(tick)
            self.stats["ticks_processed"] += 1
            logger.debug(f"Updated order book for {tick.symbol}: {book}")

            # Get current positions (symbol -> net quantity)
            try:
                current_positions = {
                    symbol: pos["net_qty"]
                    for symbol, pos in self.pnl_calc.get_positions_summary().items()
                }
            except Exception as e:
                logger.error(f"Error fetching current positions: {e}")
                current_positions = {}

            logger.debug(f"Current positions: {current_positions}")

            # Generate trading signal with current positions
            try:
                signal = self.strategy.generate_signal(book, current_positions)
            except Exception as e:
                logger.error(f"Error generating signal: {e}")
                signal = None

            logger.debug(f"Generated signal: {signal}")

            if signal:
                self.stats["signals_generated"] += 1
                await self.process_signal(signal)

        except Exception as e:
            import traceback
            logger.error(f"Unexpected error in on_tick: {e}")
            logger.error(traceback.format_exc())



    async def process_signal(self, order: Dict[str, Any]):
        """Process a trading signal through the pipeline."""
        try:
            # Risk check
            risk_result = self.risk.check_order(order)
            
            if risk_result["status"] == "REJECTED":
                logger.warning(f"Order rejected by risk: {risk_result['reason']}")
                self.oms.update_order_status(
                    risk_result.get("order_id", "UNKNOWN"),
                    "REJECTED",
                    risk_result["reason"]
                )
                return
            
            # Submit to OMS
            self.oms.submit_order({**order, "order_id": risk_result["order_id"], "status": risk_result["status"]})
            self.stats["orders_sent"] += 1
            
            # Send to exchange
            fill_result = await self.exchange.process_order({**order, "order_id": risk_result["order_id"]})

            if "status" in fill_result and fill_result["status"] == "FILLED":
                # Update risk positions
                self.risk.apply_fill(fill_result)
                
                # Record fill in OMS
                self.oms.record_fill(fill_result)
                self.oms.update_order_status(fill_result["order_id"], "FILLED")
                
                self.stats["fills_received"] += 1
                
                logger.info(
                    f"Order filled: {fill_result['quantity']} {fill_result['symbol']} "
                    f"@ ${fill_result['price']}"
                )
                # Emit WebSocket events for dashboard
                # Market update
                book = self.orderbook.books.get(fill_result["symbol"], {})
                broadcast_update('market_update', {fill_result["symbol"]: book})
                # Order update
                recent_orders = self.oms.get_orders(limit=20)
                broadcast_update('order_update', recent_orders)
                # Positions update
                positions = self.risk.get_positions()
                broadcast_update('positions_update', positions)
            else:
                self.oms.update_order_status(
                    fill_result.get("order_id", "UNKNOWN"),
                    "REJECTED",
                    fill_result.get("reason", "EXCHANGE_REJECT")
                )
                
        except Exception as e:
            import traceback
            logger.error(f"Error processing signal: {e}")
            logger.error(f"Order: {order}")
            logger.error(f"Risk result: {risk_result if 'risk_result' in locals() else 'N/A'}")
            logger.error(f"Fill result: {fill_result if 'fill_result' in locals() else 'N/A'}")
            logger.error(traceback.format_exc())

    async def print_stats(self):
        """Print system statistics periodically."""
        while True:
            await asyncio.sleep(30)  # Every 30 seconds
            
            logger.info("=== SYSTEM STATS ===")
            logger.info(f"Ticks processed: {self.stats['ticks_processed']}")
            logger.info(f"Signals generated: {self.stats['signals_generated']}")
            logger.info(f"Orders sent: {self.stats['orders_sent']}")
            logger.info(f"Fills received: {self.stats['fills_received']}")
            
            # Show positions
            positions = self.risk.get_positions()
            if positions:
                logger.info(f"Current positions: {positions}")
            
            # Show PnL
            pnl = self.pnl_calc.calculate_realized_pnl()
            if pnl:
                total_pnl = sum(pnl.values())
                logger.info(f"Total realized PnL: ${total_pnl:.2f}")

    async def run(self):
        """Run the trading system."""
        logger.info("🚀 Starting Trading System...")
        
        try:
            # Start feed connection
            await self.feed_handler.connect()
            logger.info("✅ Connected to market data feed")
            
            # Run feed listener and stats printer concurrently
            await asyncio.gather(
                self.feed_handler.listen(),
                self.print_stats()
            )
            
        except KeyboardInterrupt:
            logger.info("Shutting down trading system...")
        except Exception as e:
            logger.error(f"System error: {e}")
        finally:
            await self.feed_handler.disconnect()

async def main():
    system = TradingSystem()
    await system.run()

if __name__ == "__main__":
    print("Starting Trading System Simulator...")
    print("Make sure market data feed is running first!")
    print("Press Ctrl+C to stop")
