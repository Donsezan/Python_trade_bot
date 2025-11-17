import time
import math
import random
from typing import List, Dict, Any

class MarketDataSimulator:
    """Generates simulated market data for backtesting."""

    def __init__(self, symbol: str = 'BTC/USDT'):
        """
        Initialize the MarketDataSimulator.
        Args:
            symbol: The trading symbol (e.g., 'BTC/USDT').
        """
        self.symbol = symbol
        self.start_time = time.time()
        self.start_price = 65000
        self.volatility = 0.2
        self.liquidity = 1000

    def _generate_price(self, current_time: float) -> float:
        """
        Generates a simulated price using a combination of sine waves and noise.
        """
        time_elapsed = current_time - self.start_time
        # Combine multiple sine waves for more complex patterns
        price = (
            self.start_price
            * (1 + 0.02 * math.sin(time_elapsed / 3600))  # Hourly cycle
            * (1 + 0.05 * math.sin(time_elapsed / 86400))  # Daily cycle
            * (1 + self.volatility * (random.random() - 0.5))  # Noise
        )
        return price

    def get_latest_candles(self, timeframe: str = '1h', limit: int = 100) -> List[List[Any]]:
        """
        Generate a list of simulated OHLCV candles.
        Args:
            timeframe: The timeframe for the candles (e.g., '1m', '5m', '1h', '1d').
            limit: The number of candles to fetch.
        Returns:
            A list of OHLCV candles.
        """
        now = time.time()
        timeframe_seconds = self._timeframe_to_seconds(timeframe)

        return [
            [
                (now - (limit - i) * timeframe_seconds) * 1000,  # timestamp
                price := self._generate_price(now - (limit - i) * timeframe_seconds),  # open
                price * (1 + self.volatility * (random.random() - 0.5) / 5),  # high
                price * (1 - self.volatility * (random.random() - 0.5) / 5),  # low
                price * (1 + self.volatility * (random.random() - 0.5) / 2),  # close
                self.liquidity * (1 + self.volatility * random.random()),  # volume
            ]
            for i in range(limit)
        ]

    def get_current_quote(self) -> Dict[str, Any]:
        """
        Generate a simulated current ticker.
        Returns:
            A dictionary containing the ticker information.
        """
        now = time.time()
        price = self._generate_price(now)

        return {
            'symbol': self.symbol,
            'timestamp': int(now * 1000),
            'datetime': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime(now)),
            'high': price * (1 + self.volatility * random.random() / 5),
            'low': price * (1 - self.volatility * random.random() / 5),
            'bid': price * 0.999,
            'ask': price * 1.001,
            'last': price,
            'close': price,
            'volume': self.liquidity * (1 + self.volatility * random.random()),
        }

    def _timeframe_to_seconds(self, timeframe: str) -> int:
        """Convert timeframe string to seconds."""
        multipliers = {'m': 60, 'h': 3600, 'd': 86400}
        unit = timeframe[-1]
        value = int(timeframe[:-1])
        return value * multipliers[unit]
