from typing import Dict, Optional
from trading_bot.interfaces.exchange_adapter import ExchangeAdapter
import time
import uuid

class MockExecutionAdapter(ExchangeAdapter):
    """A mock adapter for testing purposes."""

    def __init__(self):
        """Initialize the MockExecutionAdapter."""
        self.balance = {"USDT": 10000.0, "BTC": 0.5}
        self.orders = {}

    def get_balance(self) -> Dict[str, float]:
        """Get the account balance."""
        # Return a structure similar to ccxt fetch_balance
        return {
            "free": self.balance,
            "total": self.balance,
            "used": {k: 0.0 for k in self.balance},
            "info": "Mock Balance"
        }

    def get_ticker(self, symbol: str) -> Dict:
        """Get the latest ticker information for a symbol."""
        return {
            "symbol": symbol,
            "last": 50000.0, # Dummy price
            "bid": 49990.0,
            "ask": 50010.0,
            "timestamp": int(time.time() * 1000)
        }

    def create_order(self, symbol: str, side: str, order_type: str, amount: float, price: Optional[float] = None) -> Dict:
        """Create a new order."""
        order_id = str(uuid.uuid4())
        timestamp = int(time.time() * 1000)
        
        # Simulate filling the order immediately for market orders
        status = "closed" if order_type == "market" else "open"
        filled = amount if status == "closed" else 0.0
        
        # Update mock balance (simplified)
        base, quote = symbol.split('/')
        if side == 'buy':
            cost = amount * (price if price else 50000.0)
            if self.balance.get(quote, 0) >= cost:
                self.balance[quote] -= cost
                self.balance[base] = self.balance.get(base, 0) + amount
        elif side == 'sell':
            if self.balance.get(base, 0) >= amount:
                self.balance[base] -= amount
                self.balance[quote] = self.balance.get(quote, 0) + (amount * (price if price else 50000.0))

        order = {
            "id": order_id,
            "symbol": symbol,
            "type": order_type,
            "side": side,
            "amount": amount,
            "price": price or 50000.0,
            "cost": amount * (price or 50000.0),
            "filled": filled,
            "remaining": amount - filled,
            "status": status,
            "timestamp": timestamp,
            "average": price or 50000.0
        }
        self.orders[order_id] = order
        return order

    def cancel_order(self, order_id: str, symbol: str = None) -> bool:
        """Cancel an existing order."""
        if order_id in self.orders:
            self.orders[order_id]["status"] = "canceled"
            return True
        return False

    def fetch_order(self, order_id: str, symbol: str = None) -> Dict:
        """Fetch the details of an order."""
        return self.orders.get(order_id, {"status": "unknown"})
