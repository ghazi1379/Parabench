"""
Routes analytiques avancées :
/api/analytics/market-overview
/api/analytics/brands
/api/analytics/categories
/api/analytics/price-alerts
/api/analytics/promotions
/api/analytics/assortment-gaps
/api/analytics/brand-evolution
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from models.database import get_db
from services.analytics_service import (
    get_market_overview,
    get_brand_analysis,
    get_category_analysis,
    get_price_alerts,
    get_promotion_analysis,
    get_price_evolution_by_brand,
    get_assortment_gaps,
)

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/market-overview")
async def market_overview(db: Session = Depends(get_db)):
    return get_market_overview(db)


@router.get("/brands")
async def brands_analysis(limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    return get_brand_analysis(db, limit)


@router.get("/categories")
async def categories_analysis(db: Session = Depends(get_db)):
    return get_category_analysis(db)


@router.get("/price-alerts")
async def price_alerts(
    threshold: float = Query(20.0, ge=0),
    db: Session = Depends(get_db)
):
    return get_price_alerts(db, threshold)


@router.get("/promotions")
async def promotions_analysis(db: Session = Depends(get_db)):
    return get_promotion_analysis(db)


@router.get("/brand-evolution")
async def brand_evolution(
    brand: str,
    days: int = Query(60, ge=7, le=365),
    db: Session = Depends(get_db)
):
    return get_price_evolution_by_brand(db, brand, days)


@router.get("/assortment-gaps")
async def assortment_gaps(db: Session = Depends(get_db)):
    return get_assortment_gaps(db)
