import sqlite3
import datetime

class TradeLogger:
    def __init__(self, db_path="trading_bot.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        # Create tables for decisions, trades, and market snapshots
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                symbol TEXT,
                decision TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                symbol TEXT,
                side TEXT,
                price REAL,
                amount REAL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                symbol TEXT,
                price REAL
            )
        """)
        self.conn.commit()

    def log_decision(self, symbol, decision):
        timestamp = datetime.datetime.utcnow().isoformat()
        self.cursor.execute(
            "INSERT INTO decisions (timestamp, symbol, decision) VALUES (?, ?, ?)",
            (timestamp, symbol, decision)
        )
        self.conn.commit()
        print(f"[TradeLogger] Logged decision: {symbol} -> {decision}")

    def log_trade(self, symbol, side, price, amount):
        timestamp = datetime.datetime.utcnow().isoformat()
        self.cursor.execute(
            "INSERT INTO trades (timestamp, symbol, side, price, amount) VALUES (?, ?, ?, ?, ?)",
            (timestamp, symbol, side, price, amount)
        )
        self.conn.commit()
        print(f"[TradeLogger] Logged trade: {side} {amount} {symbol} @ {price}")

    def log_snapshot(self, symbol, price):
        timestamp = datetime.datetime.utcnow().isoformat()
        self.cursor.execute(
            "INSERT INTO snapshots (timestamp, symbol, price) VALUES (?, ?, ?)",
            (timestamp, symbol, price)
        )
        self.conn.commit()
        print(f"[TradeLogger] Logged market snapshot: {symbol} price {price}")
