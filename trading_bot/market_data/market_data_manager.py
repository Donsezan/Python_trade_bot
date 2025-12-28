import ccxt
from trading_bot.config import config
from typing import List, Dict, Any
from trading_bot.market_data.market_data_simulator import MarketDataSimulator

class MarketDataManager:
    """Manages fetching of market data from the exchange or a simulator."""

    def __init__(self, backtesting: bool = False):
        """
        Initialize the MarketDataManager.
        Args:
            backtesting: If True, use the MarketDataSimulator. Otherwise, use the live exchange.
        """
        self.data_source = (
            MarketDataSimulator() if backtesting
            else self._init_exchange()
        )

    def _init_exchange(self):
        """Initializes the ccxt exchange."""
        binance_config = config.get_binance_config()
        exchange = ccxt.binance({
            'apiKey': binance_config.get('api_key'),
            'secret': binance_config.get('secret_key'),
            'options': {'defaultType': 'spot'},
        })
        if binance_config.get('sandbox', False):
            exchange.set_sandbox_mode(True)
        return exchange

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
        return (
            self.data_source.fetch_ohlcv(symbol, timeframe, limit=limit)
            if isinstance(self.data_source, ccxt.Exchange)
            else self.data_source.get_latest_candles(timeframe, limit)
        )

    def get_current_quote(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch the current ticker information for a symbol.
        Args:
            symbol: The trading symbol (e.g., 'BTC/USDT').
        Returns:
            A dictionary containing the ticker information.
        """
        return (
            self.data_source.fetch_ticker(symbol)
            if isinstance(self.data_source, ccxt.Exchange)
            else self.data_source.get_current_quote()
        )
