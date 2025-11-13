class RiskManager:
    def __init__(self, market_client, max_position_pct=0.1):
        """
        max_position_pct: maximum fraction of quote currency balance to allocate per trade.
        """
        self.client = market_client
        self.max_pct = max_position_pct

    def get_max_buy_amount(self, symbol, price):
        """
        Calculate max amount of base asset we can buy for 'symbol' without exceeding max_pct of balance.
        Assumes 'symbol' is in form 'BASE/QUOTE'.
        """
        balance = self.client.fetch_balance()
        quote_currency = symbol.split('/')[1]
        free_quote = balance.get(quote_currency, {}).get('free', 0)
        max_spend = free_quote * self.max_pct
        max_amount = max_spend / price if price and price > 0 else 0
        print(f"[RiskManager] Max buy amount for {symbol}: {max_amount} (using {self.max_pct*100:.0f}% rule)")
        return max_amount

    def can_buy(self, symbol, amount, price):
        """
        Check if buying 'amount' of base asset is within risk limits.
        """
        max_amount = self.get_max_buy_amount(symbol, price)
        return amount <= max_amount

    def can_sell(self, symbol, amount):
        """
        Check if we have enough of the asset to sell the specified amount.
        """
        balance = self.client.fetch_balance()
        base_currency = symbol.split('/')[0]
        free_base = balance.get(base_currency, {}).get('free', 0)
        print(f"[RiskManager] Available {base_currency}: {free_base}, trying to sell {amount}")
        return amount <= free_base
