import ccxt
from trading_bot.config import config
from trading_bot.interfaces.exchange_adapter import ExchangeAdapter
from typing import Dict, Optional, Any

class CCXTAdapter(ExchangeAdapter):
    """An adapter for the CCXT library."""

    def __init__(self):
        """Initialize the CCXTAdapter."""
        binance_config = config.get_binance_config()
        self.exchange = ccxt.binance({
            'apiKey': binance_config.get('api_key'),
            'secret': binance_config.get('secret_key'),
            'options': {
                'defaultType': 'spot',
            },
        })
        self.exchange.set_sandbox_mode(True)

    def get_balance(self) -> Dict[str, float]:
        """Get the account balance."""
        return self.exchange.fetch_balance()

    def get_ticker(self, symbol: str) -> Dict:
        """Get the latest ticker information for a symbol."""
        return self.exchange.fetch_ticker(symbol)

    def create_order(self, symbol: str, side: str, order_type: str, amount: float, price: Optional[float] = None) -> Dict:
        """Create a new order."""
        return self.exchange.create_order(symbol, order_type, side, amount, price)

    def cancel_order(self, order_id: str, symbol: str = None) -> bool:
        """Cancel an existing order."""
        return self.exchange.cancel_order(order_id, symbol)

    def fetch_order(self, order_id: str, symbol: str = None) -> Dict:
        """Fetch the details of an order."""
        return self.exchange.fetch_order(order_id, symbol)
