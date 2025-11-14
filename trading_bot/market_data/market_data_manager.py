import ccxt
from trading_bot.config import config
from typing import List, Dict, Any

class MarketDataManager:
    """Manages fetching of market data from the exchange."""

    def __init__(self):
        """Initialize the MarketDataManager."""
        binance_config = config.get_binance_config()
        self.exchange = ccxt.binance({
            'apiKey': binance_config.get('api_key'),
            'secret': binance_config.get('secret_key'),
            'options': {
                'defaultType': 'spot',
            },
        })
        # Use the testnet for development
        self.exchange.set_sandbox_mode(True)

    def get_latest_candles(self, symbol: str, timeframe: str = '1h', limit: int = 100) -> List[List[Any]]:
        """
        Fetch the latest OHLCV candles for a symbol.

        Args:
            symbol: The trading symbol (e.g., 'BTC/USDT').
            timeframe: The timeframe for the candles (e.g., '1m', '5m', '1h', '1d').
            limit: The number of candles to fetch.

        Returns:
            A list of OHLCV candles.
        """
        return self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

    def get_current_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch the current ticker information for a symbol.

        Args:
            symbol: The trading symbol (e.g., 'BTC/USDT').

        Returns:
            A dictionary containing the ticker information.
        """
        return self.exchange.fetch_ticker(symbol)

market_data_manager = MarketDataManager()
