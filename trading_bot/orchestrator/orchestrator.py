from datetime import datetime
import time
from trading_bot.config import config
from trading_bot.logging.logger import logger
from trading_bot.market_data.market_data_manager import MarketDataManager
from trading_bot.indicators.indicators_engine import indicators_engine
from trading_bot.news.news_ingestor import news_ingestor
from trading_bot.news.news_analyzer import news_analyzer
from trading_bot.rag_store.rag_store import rag_store
from trading_bot.decision_engine.llm_decision_engine import decision_engine
from trading_bot.execution.execution_manager import ExecutionManager
from trading_bot.persistence.sqlite_persistence import persistence, Cycle

class Orchestrator:
    """Orchestrates the trading bot's cycles."""

    def __init__(self, backtesting=False):
        """Initialize the Orchestrator."""
        self.backtesting = backtesting
        self.trading_config = config.get_trading_config()
        self.cycle_interval = self.trading_config.get("cycle_interval_minutes", 10) * 60
        self.market_data_manager = MarketDataManager(backtesting=self.backtesting)
        self.execution_manager = ExecutionManager(market_data_manager=self.market_data_manager, backtesting=self.backtesting)
        
        # Initialize Dashboard
        from trading_bot.dashboard.server import DashboardServer
        self.dashboard = DashboardServer(self)
        self.dashboard.run()

    def run(self):
        """Run the trading bot in a loop."""
        logger.info("Starting trading bot...")
        while True:
            self._run_cycle()
            if self.backtesting:
                break
            time.sleep(self.cycle_interval)

    def _run_cycle(self):
        """Execute a single trading cycle."""
        logger.info("Running trading cycle...")
        cycle = Cycle(status="running")
        persistence.save(cycle)

        try:
            # 1. Fetch market data
            symbol = self.trading_config.get("symbol", "BTC/USDT")
            timeframes = ["1h", "4h", "1d"]
            candles = {tf: self.market_data_manager.get_latest_candles(symbol, tf) for tf in timeframes}
            ticker = self.market_data_manager.get_current_quote(symbol)

            # 2. Compute indicators
            indicators = {tf: indicators_engine.get_all_indicators(candles[tf]) for tf in timeframes}

            # 3. Ingest and analyze news
            last_cycle = persistence.get_last_completed_cycle()
            last_run_time = last_cycle.ended_at if last_cycle else None
            news_articles = news_ingestor.fetch_cointelegraph_news(last_run_time=last_run_time)
            news_analyzer.process_news(news_articles)

            # 4. Retrieve news from RAG store
            rag_news = rag_store.get_latest_news()

            # 5. Get a trading decision
            context = {
                "candles": candles,
                "ticker": ticker,
                "indicators": indicators,
                "news": rag_news,
            }
            decision = decision_engine.decide(context)

            # 6. Execute the trade
            self.execution_manager.execute_trade(decision)

            cycle.SetStatus("completed")
            cycle.SetEnded_at(datetime.now())
            persistence.save(cycle)
            logger.info("Trading cycle completed successfully.")

        except Exception as e:
            cycle.SetStatus("failed")
            cycle.SetEnded_at(datetime.now())
            cycle.SetLogs(str(e))
            persistence.save(cycle)
            logger.error(f"Trading cycle failed: {e}")
