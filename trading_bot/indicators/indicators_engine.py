from typing import Dict, Any, List
import pandas as pd
import pandas_ta as ta

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
        return df.ta.ema(length=length).iloc[-1]

    def get_sma(self, df: pd.DataFrame, length: int = 12) -> float:
        """Get the Simple Moving Average (SMA)."""
        return df.ta.sma(length=length).iloc[-1]

    def get_rsi(self, df: pd.DataFrame, length: int = 14) -> float:
        """Get the Relative Strength Index (RSI)."""
        return df.ta.rsi(length=length).iloc[-1]

    def get_macd(self, df: pd.DataFrame) -> Dict[str, float]:
        """Get the Moving Average Convergence Divergence (MACD)."""
        macd = df.ta.macd()
        return {
            "macd": macd['MACD_12_26_9'].iloc[-1],
            "signal": macd['MACDs_12_26_9'].iloc[-1],
            "hist": macd['MACDh_12_26_9'].iloc[-1],
        }

    def get_atr(self, df: pd.DataFrame, length: int = 14) -> float:
        """Get the Average True Range (ATR)."""
        return df.ta.atr(length=length).iloc[-1]

    def get_volume(self, df: pd.DataFrame) -> float:
        """Get the trading volume."""
        return df['volume'].iloc[-1]

    def get_vwap(self, df: pd.DataFrame) -> float:
        """Get the Volume-Weighted Average Price (VWAP)."""
        return df.ta.vwap().iloc[-1]

indicators_engine = IndicatorsEngine()
