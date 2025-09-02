# WebSocket endpoints
MARKET_DATA_WS_PORT = 8765
DASHBOARD_WS_PORT = 5001

# Market data settings
SYMBOLS = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
TICK_INTERVAL = 0.1  # seconds

# Risk limits
MAX_POSITION = 500       
MAX_NOTIONAL = 1000000

# 🎯 CALIBRATED Strategy parameters for your feed (spreads: 0.01-0.10)
SPREAD_THRESHOLD = 0.03      # BUY when spread < 4 cents (bottom 40% of spreads)
SPREAD_SELL_THRESHOLD = 0.06 # SELL when spread > 7 cents (top 30% of spreads)


# Spread 0.01-0.04: BUY zone (market very tight - good entry)
# Spread 0.04-0.07: HOLD zone (neutral market)  
# Spread 0.07-0.10: SELL zone (market widening - take profits)

# Alternative: More aggressive thresholds
# SPREAD_THRESHOLD = 0.03      # BUY when spread < 3 cents (tighter entry)
# SPREAD_SELL_THRESHOLD = 0.06 # SELL when spread > 6 cents (quicker exit)


# Database
DB_PATH = "trading_data.db"