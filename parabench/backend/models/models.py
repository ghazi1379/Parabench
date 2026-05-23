from sqlalchemy import (
    Column, String, Float, Boolean, Integer, DateTime, Text, 
    ForeignKey, Index, UniqueConstraint, Enum as SAEnum
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()


class SiteEnum(str, enum.Enum):
    PARASHOP = "parashop"
    PARAFENDRI = "parafendri"
    TUNISIEPARA = "tunisiepara"


class ScrapingStatusEnum(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    site = Column(SAEnum(SiteEnum), nullable=False)
    external_id = Column(String(255))
    
    # Core product info
    name = Column(String(500), nullable=False)
    brand = Column(String(255), index=True)
    category = Column(String(255), index=True)
    subcategory = Column(String(255))
    description = Column(Text)
    
    # Pricing
    price = Column(Float)
    old_price = Column(Float)
    discount_percent = Column(Float)
    has_promotion = Column(Boolean, default=False)
    
    # Availability
    in_stock = Column(Boolean, default=True)
    
    # Identifiers
    ean = Column(String(50))
    ingredients = Column(Text)
    
    # Media & URL
    image_url = Column(Text)
    product_url = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_scraped = Column(DateTime, default=func.now())

    # Price history
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_products_site_name", "site", "name"),
        Index("ix_products_brand_site", "brand", "site"),
        UniqueConstraint("site", "product_url", name="uq_site_url"),
    )

    def __repr__(self):
        return f"<Product {self.site}:{self.name[:50]}>"


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    price = Column(Float)
    old_price = Column(Float)
    has_promotion = Column(Boolean, default=False)
    recorded_at = Column(DateTime, default=func.now())

    product = relationship("Product", back_populates="price_history")

    __table_args__ = (
        Index("ix_price_history_product_date", "product_id", "recorded_at"),
    )


class ScrapingJob(Base):
    __tablename__ = "scraping_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(100), unique=True, nullable=False)
    sites = Column(String(500))  # comma-separated list
    status = Column(SAEnum(ScrapingStatusEnum), default=ScrapingStatusEnum.PENDING)
    
    total_products = Column(Integer, default=0)
    scraped_products = Column(Integer, default=0)
    failed_products = Column(Integer, default=0)
    new_products = Column(Integer, default=0)
    updated_products = Column(Integer, default=0)
    
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    
    error_message = Column(Text)
    logs = Column(Text)

    __table_args__ = (
        Index("ix_scraping_jobs_status", "status"),
        Index("ix_scraping_jobs_created", "created_at"),
    )


class ScrapingLog(Base):
    __tablename__ = "scraping_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(100), index=True)
    site = Column(String(50))
    level = Column(String(20), default="INFO")  # INFO, WARNING, ERROR
    message = Column(Text)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index("ix_scraping_logs_job_created", "job_id", "created_at"),
    )


class BenchmarkSnapshot(Base):
    __tablename__ = "benchmark_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_name_normalized = Column(String(500), nullable=False, index=True)
    brand = Column(String(255))
    
    price_parashop = Column(Float)
    price_parafendri = Column(Float)
    price_tunisiepara = Column(Float)
    
    url_parashop = Column(Text)
    url_parafendri = Column(Text)
    url_tunisiepara = Column(Text)
    
    min_price = Column(Float)
    max_price = Column(Float)
    price_diff_percent = Column(Float)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_benchmark_brand", "brand"),
    )
