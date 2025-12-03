import unittest
import os
import sys
from unittest.mock import MagicMock, patch
from trading_bot.models import Decision
import trading_bot.orchestrator

# Add the parent directory to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestIntegration(unittest.TestCase):
    def setUp(self):
        # Set the config path to the test config
        sad = os.path.dirname(__file__)
        ssf = os.path.join(sad, '..', '..', 'config.test.yaml')
        os.environ['CONFIG_PATH'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.test.yaml'))

    @patch('trading_bot.orchestrator.orchestrator.decision_engine')
    @patch('trading_bot.orchestrator.orchestrator.rag_store')
    @patch('trading_bot.orchestrator.orchestrator.news_analyzer')
    @patch('trading_bot.orchestrator.orchestrator.news_ingestor')
    def test_market_data_to_indicators_flow(self, mock_news_ingestor, mock_news_analyzer, mock_rag_store, mock_decision_engine):
        """
        Test the flow from MarketDataSimulator -> IndicatorsEngine -> DecisionEngine.
        This verifies that the data format is compatible.
        """
        
        # Mock the return values for external services
        mock_news_ingestor.fetch_cointelegraph_news.return_value = []
        mock_news_analyzer.process_news.return_value = None
        mock_rag_store.get_latest_news.return_value = "Mock news context"
        
        # Mock decision to avoid LLM call
        mock_decision = Decision(
            action="hold",
            symbol="BTC/USDT",
            size=0.0,
            confidence=0.0,
            reason="Mock decision"
        )
        mock_decision_engine.decide.return_value = mock_decision

        from trading_bot.orchestrator.orchestrator import Orchestrator
        
        # Initialize Orchestrator in backtesting mode
        # This uses Real MarketDataSimulator and Real IndicatorsEngine (since we didn't mock it)
        orchestrator = Orchestrator(backtesting=True)
        
        # Run the orchestrator
        try:
            orchestrator.run()
        except Exception as e:
            self.fail(f"Orchestrator.run() raised exception: {e}")

        # Verify that decision_engine.decide was called with a context containing indicators
        # and that the indicators are not empty.
        args, _ = mock_decision_engine.decide.call_args
        context = args[0]
        
        self.assertIn("indicators", context)
        indicators = context["indicators"]
        self.assertIsInstance(indicators, dict)
        
        # Check for expected timeframes
        self.assertIn("1h", indicators)
        self.assertIn("4h", indicators)
        self.assertIn("1d", indicators)
        
        # Check content of indicators for one timeframe
        ind_1h = indicators["1h"]
        self.assertIn("rsi", ind_1h)
        self.assertIn("sma", ind_1h)
        self.assertIn("ema", ind_1h)
        
        # Verify values are not None (pandas_ta might return NaN if not enough data, but shouldn't be None object)
        # MarketDataSimulator generates 100 candles, which should be enough for RSI(14).
        self.assertIsNotNone(ind_1h["rsi"])
        print(f"DEBUG: RSI(1h) = {ind_1h['rsi']}")

if __name__ == '__main__':
    unittest.main()
