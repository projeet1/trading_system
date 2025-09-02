import sqlite3
import json
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit
from common.config import DB_PATH
from analytics.pnl import PnLCalculator


latest_prices = {}

# A helper function to update the latest prices from market feed
def update_market_price(symbol: str, bid: float, ask: float):
    latest_prices[symbol] = (bid + ask) / 2


app = Flask(__name__)
app.config['SECRET_KEY'] = 'trading_secret'
socketio = SocketIO(app, cors_allowed_origins="*")

pnl_calc = PnLCalculator()

def broadcast_update(event_type: str, data):
    socketio.emit(event_type, data)

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Trading System Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.6.1/socket.io.min.js" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #f0f2f5; color: #333; }
        h1, h2 { margin: 0 0 15px 0; }
        .container { max-width: 1300px; margin: 0 auto; }
        .card { background: #fff; padding: 25px; margin: 15px 0; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); transition: transform 0.2s; }
        .card:hover { transform: translateY(-3px); }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
        .metric { text-align: center; }
        .metric h3 { font-size: 18px; color: #555; }
        .metric .value { font-size: 28px; font-weight: 600; color: #007acc; margin-top: 5px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
        th, td { padding: 12px 10px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; font-weight: 600; }
        tbody tr:hover { background: #f1f5f9; }
        .buy { color: #28a745; font-weight: 500; }
        .sell { color: #dc3545; font-weight: 500; }
        .status-filled { color: #28a745; }
        .status-rejected { color: #dc3545; }
        .status-new { color: #ffc107; }
        canvas { margin-top: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Trading System Dashboard</h1>

        <!-- Metrics -->
        <div class="card">
            <h2>📊 System Metrics</h2>
            <div class="metrics">
                <div class="metric">
                    <h3>Total Orders</h3>
                    <div class="value" id="total-orders">0</div>
                </div>
                <div class="metric">
                    <h3>Filled Orders</h3>
                    <div class="value" id="filled-orders">0</div>
                </div>
                <div class="metric">
                    <h3>Total PnL</h3>
                    <div class="value" id="total-pnl">$0.00</div>
                </div>
                <div class="metric">
                    <h3>Active Symbols</h3>
                    <div class="value" id="active-symbols">0</div>
                </div>
            </div>
        </div>

        <!-- Market Table -->
        <div class="card">
            <h2>📈 Current Market Data</h2>
            <table id="market-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Bid</th>
                        <th>Ask</th>
                        <th>Spread</th>
                        <th>Mid</th>
                        <th>Last Update</th>
                    </tr>
                </thead>
                <tbody id="market-body"></tbody>
            </table>
        </div>

        <!-- Positions Table -->
        <div class="card">
            <h2>💰 Positions</h2>
            <table id="positions-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Net Position</th>
                        <th>Avg Price</th>
                        <th>Unrealized PnL</th>
                    </tr>
                </thead>
                <tbody id="positions-body"></tbody>
            </table>
        </div>

        <!-- Orders Table -->
        <div class="card">
            <h2>📋 Recent Orders</h2>
            <table id="orders-table">
                <thead>
                    <tr>
                        <th>Time</th>
                        <th>Symbol</th>
                        <th>Side</th>
                        <th>Quantity</th>
                        <th>Price</th>
                        <th>Status</th>
                        <th>Strategy</th>
                    </tr>
                </thead>
                <tbody id="orders-body"></tbody>
            </table>
        </div>

        <!-- Charts -->
        <div class="card">
            <h2>📊 PnL Over Time</h2>
            <canvas id="pnlChart" height="100"></canvas>
        </div>

        <div class="card">
            <h2>📈 Positions by Symbol</h2>
            <canvas id="positionsChart" height="100"></canvas>
        </div>
    </div>

    <script>
        const socket = io();

        // Metrics update
        function updateMetrics() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('total-orders').textContent = data.total_orders;
                    document.getElementById('filled-orders').textContent = data.filled_orders;
                    document.getElementById('total-pnl').textContent = `$${parseFloat(data.total_pnl).toFixed(2)}`;
                });
        }

        // Market table
        function updateMarketTable(books) {
            const tbody = document.getElementById('market-body');
            tbody.innerHTML = '';
            for (const [symbol, book] of Object.entries(books)) {
                const row = `
                    <tr>
                        <td><strong>${symbol}</strong></td>
                        <td>$${book.bid.toFixed(2)}</td>
                        <td>$${book.ask.toFixed(2)}</td>
                        <td>$${book.spread.toFixed(4)}</td>
                        <td>$${book.mid.toFixed(2)}</td>
                        <td>${new Date(book.timestamp * 1000).toLocaleTimeString()}</td>
                    </tr>
                `;
                tbody.innerHTML += row;
            }
        }

        // Orders table
        function updateOrdersTable(orders) {
            const tbody = document.getElementById('orders-body');
            tbody.innerHTML = '';
            orders.slice(0, 20).forEach(order => {
                const sideClass = order.side === 'BUY' ? 'buy' : 'sell';
                const statusClass = `status-${order.status.toLowerCase()}`;
                const row = `
                    <tr>
                        <td>${new Date(order.timestamp * 1000).toLocaleTimeString()}</td>
                        <td><strong>${order.symbol}</strong></td>
                        <td class="${sideClass}">${order.side}</td>
                        <td>${order.quantity}</td>
                        <td>${order.price.toFixed(2)}</td>
                        <td class="${statusClass}">${order.status}</td>
                        <td>${order.strategy || 'Manual'}</td>
                    </tr>
                `;
                tbody.innerHTML += row;
            });
        }

        // Positions table
        function updatePositionsTable(positions) {
            const tbody = document.getElementById('positions-body');
            tbody.innerHTML = '';
            for (const [symbol, pos] of Object.entries(positions)) {
                if (pos.net_qty !== 0) {
                    const unrealizedPnl = 0; // Needs current price
                    const row = `
                        <tr>
                            <td><strong>${symbol}</strong></td>
                            <td>${pos.net_qty}</td>
                            <td>${pos.avg_price.toFixed(2)}</td>
                            <td>${unrealizedPnl.toFixed(2)}</td>
                        </tr>
                    `;
                    tbody.innerHTML += row;
                }
            }
        }

        // Charts
        const pnlCtx = document.getElementById('pnlChart').getContext('2d');
        const positionsCtx = document.getElementById('positionsChart').getContext('2d');

        const pnlChart = new Chart(pnlCtx, {
            type: 'line',
            data: { labels: [], datasets: [{ label: 'Total PnL', data: [], borderColor: '#007acc', backgroundColor: 'rgba(0,122,204,0.2)', tension: 0.2 }] },
            options: { responsive: true, scales: { x: { title: { display: true, text: 'Time' } }, y: { title: { display: true, text: 'PnL ($)' } } } }
        });

        const positionsChart = new Chart(positionsCtx, {
            type: 'bar',
            data: { labels: [], datasets: [{ label: 'Net Position', data: [], backgroundColor: 'rgba(40,167,69,0.6)' }] },
            options: { responsive: true, scales: { y: { beginAtZero: true } } }
        });

        socket.on('market_update', data => {
            updateMarketTable(data);
            document.getElementById('active-symbols').textContent = Object.keys(data).length;
            updateMetrics();
        });

        socket.on('order_update', data => {
            updateOrdersTable(data);
            updateMetrics();
        });

        socket.on('positions_update', data => {
            updatePositionsTable(data);
            updateMetrics();

            // Update positions chart
            const symbols = [];
            const netPositions = [];
            for (const [symbol, pos] of Object.entries(data)) {
                if (pos.net_qty !== 0) { symbols.push(symbol); netPositions.push(pos.net_qty); }
            }
            positionsChart.data.labels = symbols;
            positionsChart.data.datasets[0].data = netPositions;
            positionsChart.update();
        });

        socket.on('pnl_update', data => {
            pnlChart.data.labels = data.map(d => new Date(d.timestamp * 1000).toLocaleTimeString());
            pnlChart.data.datasets[0].data = data.map(d => d.pnl);
            pnlChart.update();
        });

        // Initial load
        updateMetrics();
        setInterval(updateMetrics, 5000);
    </script>
</body>
</html>
'''

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)


@app.route('/api/metrics')
def get_metrics():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'FILLED'")
    filled_orders = cursor.fetchone()[0]
    
    conn.close()
    
    # Realized PnL
    realized_pnl_by_symbol = pnl_calc.calculate_realized_pnl()
    total_realized_pnl = sum(realized_pnl_by_symbol.values())
    
    # Unrealized PnL
    positions = pnl_calc.get_positions_summary()
    total_unrealized_pnl = 0.0
    for symbol, pos in positions.items():
        mid_price = latest_prices.get(symbol)
        if mid_price is not None:
            unrealized = (mid_price - pos['avg_price']) * pos['net_qty']
            total_unrealized_pnl += unrealized

    total_pnl = total_realized_pnl + total_unrealized_pnl

    return {
        'total_orders': total_orders,
        'filled_orders': filled_orders,
        'total_pnl': total_pnl
    }

# if __name__ == '__main__':
#     print("Starting dashboard at http://localhost:5000")
#     socketio.run(app, host='0.0.0.0', port=5000, debug=False)
