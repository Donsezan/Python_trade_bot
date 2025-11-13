from abc import ABC, abstractmethod
from typing import Dict, Optional

class ExchangeAdapter(ABC):
    """Abstract base class for an exchange adapter."""

    @abstractmethod
    def get_balance(self) -> Dict[str, float]:
        """Get the account balance."""
        pass

    @abstractmethod
    def get_ticker(self, symbol: str) -> Dict:
        """Get the latest ticker information for a symbol."""
        pass

    @abstractmethod
    def create_order(self, symbol: str, side: str, order_type: str, amount: float, price: Optional[float] = None) -> Dict:
        """Create a new order."""
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order."""
        pass

    @abstractmethod
    def fetch_order(self, order_id: str) -> Dict:
        """Fetch the details of an order."""
        pass
