from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, func
from sqlalchemy.orm import declarative_base, sessionmaker

DB_URL = "sqlite:///competitor_flipkart.db"
engine = create_engine(DB_URL, future=True, echo=False)
Session = sessionmaker(bind=engine, future=True)
Base = declarative_base()

class ProductSnapshot(Base):
    __tablename__ = "product_snapshots"   # <-- fix from _tablename_ to __tablename__
    id = Column(Integer, primary_key=True)
    platform = Column(String, index=True)
    product_id = Column(String, index=True)
    title = Column(String)
    price = Column(Float)
    list_price = Column(Float, nullable=True)
    discount_pct = Column(Float, nullable=True)
    currency = Column(String, default="INR")
    promotions = Column(JSON, nullable=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    raw = Column(JSON)

Base.metadata.create_all(engine)