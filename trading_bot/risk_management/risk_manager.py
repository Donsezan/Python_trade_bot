from trading_bot.config import config
from trading_bot.models.decision import Decision
from trading_bot.market_data.market_data_manager import MarketDataManager
from typing import Tuple

class RiskManager:
    """Enforces risk management rules."""

    def __init__(self, market_data_manager: MarketDataManager):
        """
        Initialize the RiskManager.
        Args:
            market_data_manager: An instance of MarketDataManager.
        """
        self.risk_config = config.get_risk_management_config()
        self.market_data_manager = market_data_manager

    def validate_decision(self, decision: Decision, balance: float) -> Tuple[bool, Decision]:
        """
        Validate and adjust a trading decision based on risk management rules.

        Args:
            decision: The trading decision to validate.
            balance: The current account balance.

        Returns:
            A tuple containing a boolean indicating if the decision is valid,
            and the (potentially adjusted) decision.
        """
        max_position_size = self.risk_config.get("max_position_size", 0.1)
        per_trade_risk_cap = self.risk_config.get("per_trade_risk_cap", 0.01)

        current_price = self.get_current_price(decision.symbol)
        trade_value = decision.size * (decision.price or current_price)
        max_position_value = balance * max_position_size

        if trade_value > max_position_value:
            decision.size = max_position_value / (decision.price or current_price)
            decision.reason += " (Adjusted for max position size)"

        if trade_value > balance * per_trade_risk_cap:
            decision.reason += " (Exceeds per-trade risk cap)"
            return False, decision

        return True, decision

    def get_current_price(self, symbol: str) -> float:
        """
        Get the current price of a symbol.
        """
        ticker = self.market_data_manager.get_current_quote(symbol)
        return ticker.get("last", 0.0)
