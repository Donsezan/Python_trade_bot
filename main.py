import asyncio
import time
from datetime import datetime
from core.config import Config
from core.exchange import ExchangeConnector
from core.database import Database
from core.logger import setup_logger
from core.risk_manager import RiskManager
from modules.news_analyzer import NewsAnalyzer
from modules.decision_engine import DecisionEngine
from modules.indicators import IndicatorProvider


class TradingBot:
    def __init__(self):
        self.config = Config()
        self.logger = setup_logger("TradingBot", self.config.LOG_FILE)
        self.db = Database(self.config.DB_PATH)
        self.exchange = ExchangeConnector(self.config.EXCHANGE_ID, self.config.API_KEY, self.config.API_SECRET)
        self.risk_manager = RiskManager(self.config)
        self.news_analyzer = NewsAnalyzer(self.config, self.db)
        self.indicators = IndicatorProvider(self.config, self.exchange)
        self.decision_engine = DecisionEngine(self.config)
        self.heartbeat = self.config.HEARTBEAT_SECONDS

    async def run_cycle(self):
        self.logger.info(f"--- Cycle started at {datetime.utcnow()} ---")

        # Step 1: Fetch market data
        ticker = await self.exchange.fetch_ticker(self.config.SYMBOL)
        balance = await self.exchange.fetch_balance()
        indicators = await self.indicators.fetch_indicators(self.config.SYMBOL)

        # Step 2: Analyze news
        news_summary = await self.news_analyzer.analyze_latest_news()

        # Step 3: Collect context for Decision Engine
        history = self.db.get_recent_trades(limit=20)
        context = {
            "symbol": self.config.SYMBOL,
            "balance": balance,
            "market": ticker,
            "indicators": indicators,
            "news_summary": news_summary,
            "trade_history": history,
            "open_positions": self.db.get_open_positions()
        }

        # Step 4: Generate decision
        decision_json = await self.decision_engine.make_decision(context)
        decision = decision_json.get("action")
        self.logger.info(f"Decision: {decision_json}")

        # Step 5: Risk & Action Execution
        if decision in ["buy", "sell"]:
            amount = self.risk_manager.calculate_trade_amount(balance, ticker, decision)
            order = await self.exchange.execute_trade(self.config.SYMBOL, decision, amount)
            self.db.log_trade(decision, amount, ticker['last'], order)
            self.logger.info(f"Executed {decision.upper()} order: {order}")
        elif decision == "hold":
            self.logger.info("Holding position.")
        elif decision == "pass":
            self.logger.info("Waiting for next opportunity.")

        self.logger.info(f"--- Cycle completed ---\n")

    async def run(self):
        while True:
            try:
                await self.run_cycle()
            except Exception as e:
                self.logger.exception(f"Error in cycle: {e}")
            await asyncio.sleep(self.heartbeat)


if __name__ == "__main__":
    bot = TradingBot()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\nBot stopped manually.")
