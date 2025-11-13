from trading_bot.interfaces import ExchangeAdapter as ExchangeAdapterInterface
from typing import Dict, Optional

class CCXTAdapter(ExchangeAdapterInterface):
    """An exchange adapter for Binance using CCXT."""

    def get_balance(self) -> Dict[str, float]:
        """Get the account balance."""
        pass

    def get_ticker(self, symbol: str) -> Dict:
        """Get the latest ticker information for a symbol."""
        pass

    def create_order(self, symbol: str, side: str, order_type: str, amount: float, price: Optional[float] = None) -> Dict:
        """Create a new order."""
        pass

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an existing order."""
        pass

    def fetch_order(self, order_id: str) -> Dict:
        """Fetch the details of an order."""
        pass
