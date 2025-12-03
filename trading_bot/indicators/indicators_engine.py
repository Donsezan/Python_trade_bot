from typing import Dict, Any, List
import pandas as pd
try:
    import ta
    from ta.trend import EMAIndicator, SMAIndicator, MACD
    from ta.momentum import RSIIndicator
    from ta.volatility import AverageTrueRange
    from ta.volume import VolumeWeightedAveragePrice
except ImportError:
    ta = None

class IndicatorsEngine:
    """Computes technical indicators."""

    def __init__(self):
        """Initialize the IndicatorsEngine."""
        pass

    def get_all_indicators(self, candles: List[List[Any]]) -> Dict[str, Any]:
        """
        Compute all technical indicators for a given symbol and timeframe.

        Args:
            candles: A list of OHLCV candles.

        Returns:
            A dictionary containing the computed indicators.
        """
        df = self._candles_to_dataframe(candles)
        return {
            "ema": self.get_ema(df),
            "sma": self.get_sma(df),
            "rsi": self.get_rsi(df),
            "macd": self.get_macd(df),
            "atr": self.get_atr(df),
            "volume": self.get_volume(df),
            "vwap": self.get_vwap(df),
        }

    def _candles_to_dataframe(self, candles: List[List[Any]]) -> pd.DataFrame:
        """Converts a list of OHLCV candles to a pandas DataFrame."""
        df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

    def get_ema(self, df: pd.DataFrame, length: int = 12) -> float:
        """Get the Exponential Moving Average (EMA)."""
        if ta is None: return 0.0
        indicator = EMAIndicator(close=df['close'], window=length)
        return indicator.ema_indicator().iloc[-1]

    def get_sma(self, df: pd.DataFrame, length: int = 12) -> float:
        """Get the Simple Moving Average (SMA)."""
        if ta is None: return 0.0
        indicator = SMAIndicator(close=df['close'], window=length)
        return indicator.sma_indicator().iloc[-1]

    def get_rsi(self, df: pd.DataFrame, length: int = 14) -> float:
        """Get the Relative Strength Index (RSI)."""
        if ta is None: return 50.0
        indicator = RSIIndicator(close=df['close'], window=length)
        return indicator.rsi().iloc[-1]

    def get_macd(self, df: pd.DataFrame) -> Dict[str, float]:
        """Get the Moving Average Convergence Divergence (MACD)."""
        if ta is None:
            return {"macd": 0.0, "signal": 0.0, "hist": 0.0}
        indicator = MACD(close=df['close'])
        return {
            "macd": indicator.macd().iloc[-1],
            "signal": indicator.macd_signal().iloc[-1],
            "hist": indicator.macd_diff().iloc[-1],
        }

    def get_atr(self, df: pd.DataFrame, length: int = 14) -> float:
        """Get the Average True Range (ATR)."""
        if ta is None: return 0.0
        indicator = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=length)
        return indicator.average_true_range().iloc[-1]

    def get_volume(self, df: pd.DataFrame) -> float:
        """Get the trading volume."""
        return df['volume'].iloc[-1]

    def get_vwap(self, df: pd.DataFrame) -> float:
        """Get the Volume-Weighted Average Price (VWAP)."""
        if ta is None: return 0.0
        indicator = VolumeWeightedAveragePrice(high=df['high'], low=df['low'], close=df['close'], volume=df['volume'])
        return indicator.volume_weighted_average_price().iloc[-1]

indicators_engine = IndicatorsEngine()
