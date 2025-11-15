from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, LargeBinary
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
from trading_bot.config import config
import os

Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'
    id = Column(Integer, primary_key=True)
    order_id = Column(String)
    symbol = Column(String)
    side = Column(String)
    size = Column(Float)
    price = Column(Float)
    status = Column(String)
    filled_size = Column(Float)
    requested_at = Column(DateTime)
    completed_at = Column(DateTime)
    cycle_id = Column(Integer)
    reason = Column(Text)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    order_id = Column(String, unique=True)
    symbol = Column(String)
    side = Column(String)
    order_type = Column(String)
    amount = Column(Float)
    price = Column(Float)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.now)

class Cycle(Base):
    __tablename__ = 'cycles'
    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, default=datetime.now)
    ended_at = Column(DateTime)
    status = Column(String, default='created', nullable=False)
    logs = Column(Text)
    
    def SetStatus(self, status: str):
        self.status = status

    def SetEnded_at(self, ended_at: datetime):
        self.ended_at = ended_at

    def SetLogs(self, logs: str):
        self.logs = logs

class NewsRAG(Base):
    __tablename__ = 'news_rag'
    id = Column(Integer, primary_key=True)
    title = Column(Text)
    summary = Column(Text)
    source = Column(String)
    published_at = Column(DateTime)
    fingerprint = Column(String, unique=True)
    embedding = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

class IndicatorCache(Base):
    __tablename__ = 'indicators_cache'
    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    timeframe = Column(String)
    indicator = Column(String)
    value = Column(Float)
    timestamp = Column(DateTime)

class ConfigSnapshot(Base):
    __tablename__ = 'config_snapshots'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    config_data = Column(Text)

class SQLitePersistence:
    """Handles persistence of data to an SQLite database."""

    def __init__(self, db_path: str = None):
        """Initialize the SQLitePersistence layer."""
        if db_path is None:
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'trading_bot.db')
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        """Get a new database session."""
        return self.Session()

    def save(self, obj):
        """Save a generic object to the database."""
        session = self.get_session()
        session.add(obj)
        session.commit()
        session.close()

# Create a global persistence instance
persistence = SQLitePersistence()
