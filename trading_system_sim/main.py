# import asyncio
# from analytics.dashboard import socketio, app
# from main_trading_system import TradingSystem

# async def start_trading_system():
#     system = TradingSystem()
#     await system.run()

# if __name__ == "__main__":
#     print("Starting Trading System + Dashboard...")

#     # Start trading system as a background task in SocketIO's loop
#     socketio.start_background_task(lambda: asyncio.run(start_trading_system()))

#     # Start Flask + SocketIO server
#     socketio.run(app, host="0.0.0.0", port=5000)

import asyncio
from analytics.dashboard import socketio, app
from main_trading_system import TradingSystem

async def trading_system_main():
    """Main coroutine for the trading system."""
    system = TradingSystem()
    try:
        await system.run()
    except asyncio.CancelledError:
        print("Trading system task cancelled. Shutting down...")
    except Exception as e:
        print(f"Trading system error: {e}")

def start_trading_system():
    """
    Entry point for the trading system in its own thread.
    Creates and runs an event loop bound to that thread.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(trading_system_main())
    loop.run_forever()

if __name__ == "__main__":
    print("Starting Trading System + Dashboard...")

    # ✅ Start trading system coroutine in its own event loop thread
    socketio.start_background_task(start_trading_system)

    # Run Flask + SocketIO server
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)

