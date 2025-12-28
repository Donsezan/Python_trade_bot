import asyncio
import threading
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

# Configure logging
logger = logging.getLogger("Dashboard")

class DashboardServer:
    def __init__(self, orchestrator, host="127.0.0.1", port=8000):
        self.orchestrator = orchestrator
        self.host = host
        self.port = port
        self.app = FastAPI()
        self.server_thread = None
        self.setup_routes()

    def setup_routes(self):
        # Mount static files
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        static_dir = os.path.join(current_dir, "static")
        templates_dir = os.path.join(current_dir, "templates")
        
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)

        self.app.mount("/static", StaticFiles(directory=static_dir), name="static")
        self.templates = Jinja2Templates(directory=templates_dir)

        @self.app.get("/")
        async def read_root(request: Request):
            return self.templates.TemplateResponse("index.html", {"request": request})

        @self.app.get("/api/history")
        async def get_history():
            # Retrieve recent trades/cycles from persistence
            from trading_bot.persistence.sqlite_persistence import persistence, Cycle, Trade
            session = persistence.get_session()
            try:
                # Fetch last 20 trades
                trades = session.query(Trade).order_by(Trade.completed_at.desc()).limit(20).all()
                trades_data = []
                for t in trades:
                    trades_data.append({
                        "id": t.id,
                        "symbol": t.symbol,
                        "side": t.side,
                        "size": t.size,
                        "price": t.price,
                        "status": t.status,
                        "time": t.completed_at.isoformat() if t.completed_at else None,
                        "profit": 0 # Placeholder, logic to calculate profit needed if applicable
                    })
                
                # Fetch recent logs/cycles
                cycles = session.query(Cycle).order_by(Cycle.ended_at.desc()).limit(10).all()
                cycles_data = []
                for c in cycles:
                    cycles_data.append({
                        "id": c.id,
                        "status": c.status,
                        "time": c.ended_at.isoformat() if c.ended_at else None,
                        "logs": c.logs
                    })

                return {"trades": trades_data, "cycles": cycles_data}
            except Exception as e:
                logger.error(f"Error fetching history: {e}")
                return {"trades": [], "cycles": []}
            finally:
                session.close()

        @self.app.get("/api/market_data")
        async def get_market_data():
            # Get latest candles for the active symbol
            symbol = self.orchestrator.trading_config.get("symbol", "BTC/USDT")
            timeframe = "1h" # Default timeframe for chart
            try:
                candles = self.orchestrator.market_data_manager.get_latest_candles(symbol, timeframe, limit=100)
                
                # Check if it's a list (from ccxt or simulator)
                if isinstance(candles, list):
                    data = []
                    for candle in candles:
                        # CCXT format: [timestamp, open, high, low, close, volume]
                        data.append({
                            "time": candle[0],
                            "open": candle[1],
                            "high": candle[2],
                            "low": candle[3],
                            "close": candle[4]
                        })
                    return {"symbol": symbol, "timeframe": timeframe, "data": data}
                # Fallback for DataFrame if ever used in future
                elif hasattr(candles, 'to_dict'):
                     # Convert DataFrame to list of dicts: time, open, high, low, close
                    data = []
                    for index, row in candles.iterrows():
                        # specific mapping depending on dataframe structure
                        # Assuming index is datetime or 'timestamp' column exists
                        ts = index.timestamp() * 1000 if hasattr(index, 'timestamp') else row.get('timestamp')
                        data.append({
                            "time": ts,
                            "open": row['open'],
                            "high": row['high'],
                            "low": row['low'],
                            "close": row['close']
                        })
                    return {"symbol": symbol, "timeframe": timeframe, "data": data}
                else:
                    return {"symbol": symbol, "data": []}
            except Exception as e:
                logger.error(f"Error fetching market data: {e}")
                return {"symbol": symbol, "data": []}

        @self.app.get("/api/status")
        async def get_status():
            try:
                balance = self.orchestrator.execution_manager.get_balance()
                # Extract relevant balance info (e.g., USDT free/total)
                # Structure depends on CCXT response
                total_balance = balance.get("total", {})
                free_balance = balance.get("free", {})
                
                # Current active cycle status
                # logic to get current running status from orchestrator if exposed, or persistence
                current_status = "Idle"
                # This is a bit tricky since Orchestrator run loop is blocking.
                # We might need Orchestrator to update a status flag we can read.
                
                return {
                    "balance": {
                        "total": total_balance,
                        "free": free_balance
                    },
                    "status": current_status
                }
            except Exception as e:
                logger.error(f"Error fetching status: {e}")
                return {}

    def run(self):
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()

    def _run_server(self):
        uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")
