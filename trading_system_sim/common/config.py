# WebSocket endpoints
MARKET_DATA_WS_PORT = 8765
DASHBOARD_WS_PORT = 5001

# Market data settings
SYMBOLS = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
TICK_INTERVAL = 0.1  # seconds

# Risk limits
MAX_POSITION = 1000
MAX_NOTIONAL = 1000000

# Strategy parameters
SPREAD_THRESHOLD = 0.05  # buy if spread < 5 cents
SPREAD_SELL_THRESHOLD = 0.10
# Database
DB_PATH = "trading_data.db"
