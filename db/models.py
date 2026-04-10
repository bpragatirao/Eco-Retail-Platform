"""
SQLAlchemy ORM models for the Eco-Retail Platform.
Maps to the schema defined in db/schema.sql.
"""

from datetime import date, datetime
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey, Text,
    create_engine, Index
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from config import DATABASE_URL

Base = declarative_base()


class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    base_price = Column(Float, nullable=False)
    unit = Column(String, default="unit")
    min_margin = Column(Float, default=0.10)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    batches = relationship("InventoryBatch", back_populates="product")
    transactions = relationship("Transaction", back_populates="product")
    pricing_history = relationship("PricingHistory", back_populates="product")
    waste_logs = relationship("WasteLog", back_populates="product")

    def __repr__(self):
        return f"<Product(id={self.product_id}, name='{self.name}', category='{self.category}')>"


class InventoryBatch(Base):
    __tablename__ = "inventory_batches"

    batch_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    remaining_quantity = Column(Integer, nullable=False)
    expiry_date = Column(Date, nullable=False)
    arrival_date = Column(Date, default=date.today)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="batches")
    transactions = relationship("Transaction", back_populates="batch")

    @property
    def days_to_expiry(self) -> int:
        """Calculate days remaining until expiry."""
        return (self.expiry_date - date.today()).days

    @property
    def is_near_expiry(self) -> bool:
        """Check if batch is within 3 days of expiry."""
        return self.days_to_expiry <= 3

    def __repr__(self):
        return (
            f"<InventoryBatch(id={self.batch_id}, product={self.product_id}, "
            f"remaining={self.remaining_quantity}, expiry={self.expiry_date})>"
        )


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("inventory_batches.batch_id"), nullable=True)
    quantity_sold = Column(Integer, nullable=False)
    sale_price = Column(Float, nullable=False)
    original_price = Column(Float, nullable=True)
    discount_pct = Column(Float, default=0.0)
    sale_date = Column(Date, default=date.today)
    sale_timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="transactions")
    batch = relationship("InventoryBatch", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction(id={self.transaction_id}, qty={self.quantity_sold}, price={self.sale_price})>"


class PricingHistory(Base):
    __tablename__ = "pricing_history"

    pricing_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("inventory_batches.batch_id"), nullable=True)
    original_price = Column(Float, nullable=False)
    dynamic_price = Column(Float, nullable=False)
    discount_pct = Column(Float, default=0.0)
    waste_risk_score = Column(Float, nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="pricing_history")

    def __repr__(self):
        return (
            f"<PricingHistory(product={self.product_id}, "
            f"original={self.original_price}, dynamic={self.dynamic_price})>"
        )


class WasteLog(Base):
    __tablename__ = "waste_log"

    waste_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("inventory_batches.batch_id"), nullable=False)
    quantity_wasted = Column(Integer, nullable=False)
    value_lost = Column(Float, nullable=False)
    waste_date = Column(Date, default=date.today)
    reason = Column(String, default="expired")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="waste_logs")

    def __repr__(self):
        return f"<WasteLog(product={self.product_id}, qty={self.quantity_wasted}, lost=₹{self.value_lost})>"


# ── Engine & Session Factory ─────────────────────────────────────────────────

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    """Create all tables in the database."""
    Base.metadata.create_all(engine)


def get_session():
    """Get a new database session."""
    return SessionLocal()
