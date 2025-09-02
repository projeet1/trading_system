1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the system (in separate terminals):
```bash
# Terminal 1: Market Data Feed
python market_data/feed_generator.py

# Terminal 2: Main Trading System
python main.py

# Terminal 3: Dashboard
python analytics/dashboard.py
```

3. Open dashboard at http://localhost:5000