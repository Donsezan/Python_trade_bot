import unittest
import os
import sys
from unittest.mock import MagicMock, patch
from trading_bot.models.decision import Decision

# Add the parent directory to the python path so we can import the package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestSmoke(unittest.TestCase):
    def setUp(self):
        # Set the config path to the test config
        os.environ['CONFIG_PATH'] = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.test.yaml'))

    @patch('trading_bot.orchestrator.orchestrator.persistence')
    @patch('trading_bot.orchestrator.orchestrator.ExecutionManager')
    @patch('trading_bot.orchestrator.orchestrator.MarketDataManager')
    @patch('trading_bot.orchestrator.orchestrator.logger')
    @patch('trading_bot.orchestrator.orchestrator.indicators_engine')
    @patch('trading_bot.orchestrator.orchestrator.decision_engine')
    @patch('trading_bot.orchestrator.orchestrator.rag_store')
    @patch('trading_bot.orchestrator.orchestrator.news_analyzer')
    @patch('trading_bot.orchestrator.orchestrator.news_ingestor')
    def test_orchestrator_run_cycle(self, mock_news_ingestor, mock_news_analyzer, mock_rag_store, mock_decision_engine, mock_indicators_engine, mock_logger, mock_market_data_manager_cls, mock_execution_manager_cls, mock_persistence):
        """Test that the orchestrator can run a single cycle in backtesting mode."""
        
        # Mock the return values
        mock_news_ingestor.fetch_cointelegraph_news.return_value = []
        mock_news_analyzer.process_news.return_value = None
        mock_rag_store.get_latest_news.return_value = "Mock news context"
        mock_indicators_engine.get_all_indicators.return_value = {}
        
        # Setup new mocks
        mock_market_data_manager = mock_market_data_manager_cls.return_value
        mock_market_data_manager.get_latest_candles.return_value = []
        mock_market_data_manager.get_current_quote.return_value = 50000.0
        
        mock_execution_manager = mock_execution_manager_cls.return_value

        # Mock decision
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
        orchestrator = Orchestrator(backtesting=True)
        
        # Run the orchestrator (should run one cycle and exit)
        try:
            orchestrator.run()
        except Exception as e:
            self.fail(f"Orchestrator.run() raised exception: {e}")

        # Verify that the mocks were called
        mock_news_ingestor.fetch_cointelegraph_news.assert_called_once()
        mock_news_analyzer.process_news.assert_called_once()
        mock_rag_store.get_latest_news.assert_called_once()
        mock_decision_engine.decide.assert_called_once()
        mock_indicators_engine.get_all_indicators.assert_called()
        
        # Verify new mocks were called
        mock_market_data_manager.get_latest_candles.assert_called()
        mock_market_data_manager.get_current_quote.assert_called()
        mock_execution_manager.execute_trade.assert_called_once_with(mock_decision)
        mock_persistence.save.assert_called()

if __name__ == '__main__':
    unittest.main()
