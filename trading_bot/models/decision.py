from dataclasses import dataclass
from typing import Optional

@dataclass
class Decision:
    """Data model for a trading decision."""
    action: str  # BUY, SELL, HOLD, WAIT
    symbol: str
    size: float
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    confidence: float = 0.0
    reason: str = ""
