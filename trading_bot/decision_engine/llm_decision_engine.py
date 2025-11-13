from trading_bot.interfaces import DecisionEngine as DecisionEngineInterface
from trading_bot.models import Decision
from typing import Dict

class LLMDecisionEngine(DecisionEngineInterface):
    """Makes trading decisions using an LLM."""

    def decide(self, context: Dict) -> Decision:
        """Make a trading decision based on the given context."""
        pass
