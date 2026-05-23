"""
Service d'analytique avancée : tendances, alertes, rapports de marché
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, desc, and_, case
from models.models import Product, PriceHistory, BenchmarkSnapshot


def get_market_overview(db: Session) -> Dict:
    """Vue globale du marché para tunisien"""
    total = db.query(Product).count()
    total_with_price = db.query(Product).filter(Product.price.isnot(None)).count()
    avg_price = db.query(func.avg(Product.price)).filter(Product.price.isnot(None)).scalar() or 0
    median_price = None

    # Prix par site
    site_stats = db.query(
        Product.site,
        func.count(Product.id).label("count"),
        func.avg(Product.price).label("avg_price"),
        func.min(Product.price).label("min_price"),
        func.max(Product.price).label("max_price"),
        func.count(case((Product.has_promotion == True, 1))).label("promo_count"),
    ).group_by(Product.site).all()

    return {
        "total_products": total,
        "total_with_price": total_with_price,
        "avg_price_market": round(float(avg_price), 3),
        "sites": [
            {
                "site": s.site,
                "count": s.count,
                "avg_price": round(float(s.avg_price), 3) if s.avg_price else 0,
                "min_price": round(float(s.min_price), 3) if s.min_price else 0,
                "max_price": round(float(s.max_price), 3) if s.max_price else 0,
                "promo_count": s.promo_count,
                "promo_rate": round(s.promo_count / s.count * 100, 1) if s.count else 0,
            }
            for s in site_stats
        ],
    }


def get_brand_analysis(db: Session, limit: int = 20) -> List[Dict]:
    """Analyse détaillée par marque"""
    brands = db.query(
        Product.brand,
        func.count(Product.id).label("total_products"),
        func.count(distinct(Product.site)).label("sites_count"),
        func.count(distinct(Product.category)).label("categories_count"),
        func.avg(Product.price).label("avg_price"),
        func.min(Product.price).label("min_price"),
        func.max(Product.price).label("max_price"),
        func.count(case((Product.has_promotion == True, 1))).label("promo_count"),
        func.count(case((Product.in_stock == True, 1))).label("in_stock_count"),
    ).filter(
        Product.brand.isnot(None)
    ).group_by(Product.brand).order_by(desc("total_products")).limit(limit).all()

    return [
        {
            "brand": b.brand,
            "total_products": b.total_products,
            "sites_count": b.sites_count,
            "categories_count": b.categories_count,
            "avg_price": round(float(b.avg_price), 3) if b.avg_price else 0,
            "min_price": round(float(b.min_price), 3) if b.min_price else 0,
            "max_price": round(float(b.max_price), 3) if b.max_price else 0,
            "promo_rate": round(b.promo_count / b.total_products * 100, 1) if b.total_products else 0,
            "availability_rate": round(b.in_stock_count / b.total_products * 100, 1) if b.total_products else 0,
        }
        for b in brands
    ]


def get_category_analysis(db: Session) -> List[Dict]:
    """Analyse par catégorie"""
    cats = db.query(
        Product.category,
        func.count(Product.id).label("total"),
        func.count(distinct(Product.brand)).label("brands"),
        func.count(distinct(Product.site)).label("sites"),
        func.avg(Product.price).label("avg_price"),
        func.count(case((Product.has_promotion == True, 1))).label("promos"),
    ).filter(
        Product.category.isnot(None)
    ).group_by(Product.category).order_by(desc("total")).all()

    return [
        {
            "category": c.category,
            "total_products": c.total,
            "brands_count": c.brands,
            "sites_count": c.sites,
            "avg_price": round(float(c.avg_price), 3) if c.avg_price else 0,
            "promo_rate": round(c.promos / c.total * 100, 1) if c.total else 0,
        }
        for c in cats
    ]


def get_price_alerts(db: Session, threshold_pct: float = 20.0) -> List[Dict]:
    """
    Alertes de prix : produits avec écart > threshold entre les sites
    """
    snapshots = db.query(BenchmarkSnapshot).filter(
        BenchmarkSnapshot.price_diff_percent >= threshold_pct
    ).order_by(desc(BenchmarkSnapshot.price_diff_percent)).limit(50).all()

    alerts = []
    for s in snapshots:
        prices = {
            "parashop": s.price_parashop,
            "parafendri": s.price_parafendri,
            "tunisiepara": s.price_tunisiepara,
        }
        valid = {k: v for k, v in prices.items() if v}
        if len(valid) < 2:
            continue

        min_site = min(valid, key=valid.get)
        max_site = max(valid, key=valid.get)

        alerts.append({
            "product": s.product_name_normalized,
            "brand": s.brand,
            "cheapest_site": min_site,
            "cheapest_price": valid[min_site],
            "expensive_site": max_site,
            "expensive_price": valid[max_site],
            "diff_percent": s.price_diff_percent,
            "saving": round(valid[max_site] - valid[min_site], 3),
        })

    return alerts


def get_promotion_analysis(db: Session) -> Dict:
    """Analyse des promotions en cours"""
    total_promo = db.query(Product).filter(Product.has_promotion == True).count()
    total = db.query(Product).count()

    avg_discount = db.query(
        func.avg(Product.discount_percent)
    ).filter(
        Product.has_promotion == True,
        Product.discount_percent.isnot(None)
    ).scalar() or 0

    best_promos = db.query(Product).filter(
        Product.has_promotion == True,
        Product.discount_percent.isnot(None),
    ).order_by(desc(Product.discount_percent)).limit(20).all()

    by_site = db.query(
        Product.site,
        func.count(Product.id).label("promo_count"),
        func.avg(Product.discount_percent).label("avg_discount"),
    ).filter(Product.has_promotion == True).group_by(Product.site).all()

    by_category = db.query(
        Product.category,
        func.count(Product.id).label("promo_count"),
    ).filter(
        Product.has_promotion == True,
        Product.category.isnot(None)
    ).group_by(Product.category).order_by(desc("promo_count")).limit(10).all()

    return {
        "total_promo": total_promo,
        "promo_rate": round(total_promo / total * 100, 1) if total else 0,
        "avg_discount_percent": round(float(avg_discount), 1),
        "by_site": [
            {
                "site": s.site,
                "count": s.promo_count,
                "avg_discount": round(float(s.avg_discount), 1) if s.avg_discount else 0,
            }
            for s in by_site
        ],
        "by_category": [{"category": c.category, "count": c.promo_count} for c in by_category],
        "top_discounts": [
            {
                "name": p.name,
                "brand": p.brand,
                "site": p.site,
                "price": p.price,
                "old_price": p.old_price,
                "discount_percent": p.discount_percent,
                "product_url": p.product_url,
                "image_url": p.image_url,
            }
            for p in best_promos
        ],
    }


def get_price_evolution_by_brand(db: Session, brand: str, days: int = 60) -> List[Dict]:
    """Évolution des prix pour une marque donnée"""
    since = datetime.utcnow() - timedelta(days=days)

    rows = db.query(
        func.date(PriceHistory.recorded_at).label("date"),
        Product.site,
        Product.name,
        func.avg(PriceHistory.price).label("avg_price"),
    ).join(Product).filter(
        Product.brand.ilike(f"%{brand}%"),
        PriceHistory.recorded_at >= since,
        PriceHistory.price.isnot(None),
    ).group_by(
        func.date(PriceHistory.recorded_at), Product.site, Product.name
    ).order_by("date").all()

    return [
        {
            "date": str(r.date),
            "site": r.site,
            "product": r.name,
            "avg_price": round(float(r.avg_price), 3),
        }
        for r in rows
    ]


def get_assortment_gaps(db: Session) -> List[Dict]:
    """
    Produits présents sur certains sites mais pas sur d'autres.
    Aide à identifier les manques dans l'assortiment.
    """
    # Products per site
    parashop_brands = set(
        b[0] for b in db.query(distinct(Product.brand)).filter(
            Product.site == "parashop", Product.brand.isnot(None)
        ).all()
    )
    parafendri_brands = set(
        b[0] for b in db.query(distinct(Product.brand)).filter(
            Product.site == "parafendri", Product.brand.isnot(None)
        ).all()
    )
    tunisiepara_brands = set(
        b[0] for b in db.query(distinct(Product.brand)).filter(
            Product.site == "tunisiepara", Product.brand.isnot(None)
        ).all()
    )

    all_brands = parashop_brands | parafendri_brands | tunisiepara_brands

    gaps = []
    for brand in sorted(all_brands):
        presence = {
            "parashop": brand in parashop_brands,
            "parafendri": brand in parafendri_brands,
            "tunisiepara": brand in tunisiepara_brands,
        }
        sites_count = sum(presence.values())
        if sites_count < 3:
            gaps.append({
                "brand": brand,
                "sites_count": sites_count,
                "present_on": [k for k, v in presence.items() if v],
                "missing_on": [k for k, v in presence.items() if not v],
            })

    # Sort: least distributed first
    gaps.sort(key=lambda x: x["sites_count"])
    return gaps[:100]
