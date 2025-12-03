from trading_bot.execution.ccxt_adapter import CCXTAdapter
from trading_bot.models.decision import Decision
from trading_bot.risk_management.risk_manager import RiskManager
from trading_bot.market_data.market_data_manager import MarketDataManager
from trading_bot.persistence.sqlite_persistence import persistence, Order, Trade
from datetime import datetime
import time

class ExecutionManager:
    """Manages the execution of trades."""

    def __init__(self, market_data_manager: MarketDataManager, backtesting: bool = False):
        """
        Initialize the ExecutionManager.
        Args:
            market_data_manager: An instance of MarketDataManager.
            backtesting: Whether to run in backtesting mode.
        """
        if backtesting:
            from trading_bot.execution.mock_execution_adapter import MockExecutionAdapter
            self.exchange_adapter = MockExecutionAdapter()
        else:
            self.exchange_adapter = CCXTAdapter()
            
        self.risk_manager = RiskManager(market_data_manager)

    def execute_trade(self, decision: Decision):
        """
        Execute a trade based on a decision from the DecisionEngine.

        Args:
            decision: The trading decision to execute.
        """
        balance = self.get_balance()
        is_valid, adjusted_decision = self.risk_manager.validate_decision(decision, balance.get("free", {}).get("USDT", 0))

        if is_valid:
            try:
                order_result = self.exchange_adapter.create_order(
                    symbol=adjusted_decision.symbol,
                    side=adjusted_decision.action.lower(),
                    order_type="market",
                    amount=adjusted_decision.size
                )
                self.save_order(order_result)
                self.monitor_order(order_result["id"], adjusted_decision.symbol)
            except Exception as e:
                print(f"Error executing trade: {e}")

    def get_balance(self):
        """Get the current account balance."""
        return self.exchange_adapter.get_balance()

    def save_order(self, order_result):
        """Save an order to the database."""
        order = Order(
            order_id=order_result["id"],
            symbol=order_result["symbol"],
            side=order_result["side"],
            order_type=order_result["type"],
            amount=order_result["amount"],
            price=order_result.get("price"),
            status=order_result["status"],
            created_at=datetime.fromtimestamp(order_result["timestamp"] / 1000)
        )
        persistence.save(order)

    def monitor_order(self, order_id: str, symbol: str):
        """Monitor an order and create a trade record when it's filled."""
        for _ in range(10): # 10 retries
            order = self.exchange_adapter.fetch_order(order_id, symbol)
            if order["status"] == "closed":
                trade = Trade(
                    order_id=order["id"],
                    symbol=order["symbol"],
                    side=order["side"],
                    size=order["filled"],
                    price=order["average"],
                    status="filled",
                    filled_size=order["filled"],
                    requested_at=datetime.fromtimestamp(order["timestamp"] / 1000),
                    completed_at=datetime.now(),
                    reason="LLM Decision"
                )
                persistence.save(trade)
                break
            time.sleep(6) # Wait 6 seconds before retrying
