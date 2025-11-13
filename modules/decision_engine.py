# decision_engine.py
import json
from typing import Dict, Any, Optional

# Note: import or reference RiskManager and TradeLogger from your project
# from risk_manager import RiskManager

class DecisionEngine:
    """
    DecisionEngine that drives trading decisions using an LLM thinking step.
    - Input: news_summary (aggregated), indicators dict, trade_history list, positions dict, market_snapshot dict, balance dict
    - Output: validated decision dict (JSON-friendly)
    """

    def __init__(self, risk_manager, llm_client=None):
        """
        llm_client: optional client/wrapper for a real LLM; if None use placeholder
        risk_manager: instance of RiskManager that exposes can_buy/can_sell/get_max_buy_amount etc.
        """
        self.risk_manager = risk_manager
        self.llm_client = llm_client  # future integration point

    def _compose_prompt(self, *,
                        symbol: str,
                        news_summary: Dict[str, Any],
                        indicators: Dict[str, Any],
                        positions: Dict[str, Any],
                        balance: Dict[str, Any],
                        market_snapshot: Dict[str, Any],
                        trade_history: Optional[list] = None) -> str:
        """
        Create a concise reasoning prompt for the LLM. Keep short in this placeholder.
        In real life you'd craft a much more detailed prompt template with examples and constraints.
        """
        prompt = []
        prompt.append(f"Symbol: {symbol}")
        prompt.append(f"Price: {market_snapshot.get('price')}")
        prompt.append(f"Indicators: {json.dumps(indicators)}")
        prompt.append(f"Positions: {json.dumps(positions)}")
        prompt.append(f"Balance: {json.dumps(balance)}")
        prompt.append(f"News summary: {news_summary.get('summary') or ''}")
        prompt.append(f"News sentiment: {news_summary.get('sentiment')} (score {news_summary.get('score')})")
        if trade_history:
            prompt.append(f"Recent trade history entries: {len(trade_history)}")
        prompt.append("Constraints: Return a JSON with fields action,symbol,amount,price_type,price,stop_loss,take_profit,confidence,rationale.")
        prompt.append("Available actions: buy / sell / hold / pass. Amount should be numeric base-asset quantity.")
        return "\n".join(prompt)

    def _llm_think_placeholder(self, prompt: str) -> Dict[str, Any]:
        """
        Very simple placeholder that inspects prompt to decide.
        Replace with a call to a real LLM that returns structured JSON.
        """
        # Toy logic: if "positive" present then BUY, if "negative" present then SELL, else HOLD
        low = prompt.lower()
        action = "hold"
        confidence = 0.5
        if "positive" in low and "rsi" not in low:
            action = "buy"; confidence = 0.75
        if "negative" in low:
            action = "sell"; confidence = 0.80
        # simplistic sizing: use 50% of max buy amount if buy
        # To be validated by RiskManager afterwards
        example_json = {
            "action": action,
            "symbol": "BTC/USDT",
            "amount": None,  # fill later
            "price_type": "market",
            "price": None,
            "stop_loss": None,
            "take_profit": None,
            "confidence": confidence,
            "rationale": "Derived from news sentiment + indicators via placeholder logic."
        }
        return example_json

    def decide(self, *,
               symbol: str,
               news_summary: Dict[str, Any],
               indicators: Dict[str, Any],
               positions: Dict[str, Any],
               balance: Dict[str, Any],
               market_snapshot: Dict[str, Any],
               trade_history: Optional[list] = None,
               desired_fraction_of_max: float = 0.5) -> Dict[str, Any]:
        """
        Main decision entry.
        1. Compose prompt for LLM (or placeholder)
        2. Get structured decision
        3. Validate/adjust according to RiskManager; return final JSON decision
        """
        prompt = self._compose_prompt(
            symbol=symbol,
            news_summary=news_summary,
            indicators=indicators,
            positions=positions,
            balance=balance,
            market_snapshot=market_snapshot,
            trade_history=trade_history
        )

        # call LLM (or placeholder)
        if self.llm_client:
            # Example: call your LLM wrapper with a structured response preference
            raw_decision = self.llm_client.call_llm_for_decision(prompt)
        else:
            raw_decision = self._llm_think_placeholder(prompt)

        # Ensure schema exists and symbol is set
        raw_decision.setdefault("symbol", symbol)
        action = raw_decision.get("action", "hold").lower()

        # Determine amount candidate if BUY
        final_decision = raw_decision.copy()

        price = market_snapshot.get("price")
        if action == "buy":
            # ask RiskManager for max buy amount, then scale by desired_fraction_of_max
            max_amount = self.risk_manager.get_max_buy_amount(symbol, price)
            candidate_amount = max_amount * desired_fraction_of_max
            candidate_amount = float(candidate_amount) if candidate_amount else 0.0
            if candidate_amount <= 0:
                # cannot buy -> change to hold
                final_decision.update({
                    "action": "hold",
                    "amount": 0.0,
                    "rationale": (final_decision.get("rationale","") + " -> Downgraded to HOLD due to risk/balance limits.")
                })
            else:
                final_decision["amount"] = round(candidate_amount, 8)
        elif action == "sell":
            # If sell requested but no position -> change to hold
            base = symbol.split('/')[0]
            available = positions.get(base, 0.0)
            if available <= 0:
                final_decision.update({
                    "action": "hold",
                    "amount": 0.0,
                    "rationale": (final_decision.get("rationale","") + " -> Downgraded to HOLD (no position to sell).")
                })
            else:
                # sell everything by default (or LLM-specified fraction)
                amt = final_decision.get("amount")
                if not amt:
                    amt = float(available)
                else:
                    amt = min(float(amt), float(available))
                # validate with risk manager
                if not self.risk_manager.can_sell(symbol, amt):
                    final_decision.update({
                        "action": "hold",
                        "amount": 0.0,
                        "rationale": final_decision.get("rationale", "") + " -> HOLD because RiskManager disallowed the sell amount."
                    })
                else:
                    final_decision["amount"] = round(amt, 8)
        else:
            # hold/pass -> zero amount
            final_decision["amount"] = 0.0

        # Add schema sanity fields
        final_decision.setdefault("price_type", final_decision.get("price_type", "market"))
        final_decision.setdefault("price", final_decision.get("price", None))
        final_decision.setdefault("stop_loss", final_decision.get("stop_loss", None))
        final_decision.setdefault("take_profit", final_decision.get("take_profit", None))
        final_decision.setdefault("confidence", float(final_decision.get("confidence", 0.5)))
        final_decision.setdefault("rationale", str(final_decision.get("rationale", "")))

        # final small validation: ensure action is one of allowed
        if final_decision["action"] not in ("buy", "sell", "hold", "pass"):
            final_decision["action"] = "hold"
            final_decision["rationale"] += " -> Normalized invalid action to HOLD."

        return final_decision
