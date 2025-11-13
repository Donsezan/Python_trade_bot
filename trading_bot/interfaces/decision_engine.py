from abc import ABC, abstractmethod
from typing import Dict
from trading_bot.models import Decision

class DecisionEngine(ABC):
    """Abstract base class for a decision engine."""

    @abstractmethod
    def decide(self, context: Dict) -> Decision:
        """Make a trading decision based on the given context."""
        pass
