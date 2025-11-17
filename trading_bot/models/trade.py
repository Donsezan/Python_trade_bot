from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Trade:
    """Data model for a trade record."""
    trade_id: int
    order_id: str
    symbol: str
    side: str
    size: float
    price: float
    status: str
    filled_size: float
    requested_at: datetime
    completed_at: Optional[datetime] = None
    cycle_id: int = 0
    reason: str = ""
