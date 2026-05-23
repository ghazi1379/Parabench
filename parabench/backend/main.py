import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct, desc, or_, and_
from typing import List, Optional
from datetime import datetime, timedelta
from loguru import logger

from models.database import get_db, create_tables
from models.models import Product, PriceHistory, ScrapingJob, ScrapingLog, BenchmarkSnapshot, ScrapingStatusEnum
from services.scraping_service import run_scraping_job, create_scraping_job, update_benchmark_snapshots
from services.export_service import export_csv, export_excel, export_pdf, export_benchmark_excel
from api.schemas import *
from api.analytics_routes import router as analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting ParaBench API...")
    create_tables()
    logger.info("Database tables created/verified")
    yield
    logger.info("Shutting down ParaBench API")


app = FastAPI(
    title="ParaBench API",
    description="Benchmark du marché parapharmaceutique tunisien",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(analytics_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== DASHBOARD ====================

@app.get("/api/dashboard/stats", tags=["Dashboard"])
async def get_dashboard_stats(db: Session = Depends(get_db)):
    total_products = db.query(Product).count()
    total_brands = db.query(distinct(Product.brand)).filter(Product.brand.isnot(None)).count()
    total_categories = db.query(distinct(Product.category)).filter(Product.category.isnot(None)).count()
    
    today = datetime.utcnow().date()
    promos_today = db.query(Product).filter(Product.has_promotion == True).count()
    
    avg_price = db.query(func.avg(Product.price)).filter(Product.price.isnot(None)).scalar()
    
    products_per_site = db.query(Product.site, func.count(Product.id)).group_by(Product.site).all()
    
    last_job = db.query(ScrapingJob).order_by(desc(ScrapingJob.created_at)).first()
    
    benchmark_count = db.query(BenchmarkSnapshot).count()
    
    return {
        "total_products": total_products,
        "total_brands": total_brands,
        "total_categories": total_categories,
        "promotions_count": promos_today,
        "avg_price": round(avg_price, 3) if avg_price else 0,
        "products_per_site": {site: count for site, count in products_per_site},
        "last_scraping": last_job.completed_at.isoformat() if last_job and last_job.completed_at else None,
        "benchmark_count": benchmark_count,
    }


@app.get("/api/dashboard/top-brands", tags=["Dashboard"])
async def get_top_brands(limit: int = 10, db: Session = Depends(get_db)):
    brands = db.query(
        Product.brand,
        func.count(Product.id).label("count"),
        func.avg(Product.price).label("avg_price")
    ).filter(
        Product.brand.isnot(None)
    ).group_by(Product.brand).order_by(desc("count")).limit(limit).all()
    
    return [{"brand": b, "count": c, "avg_price": round(p, 3) if p else 0} for b, c, p in brands]


@app.get("/api/dashboard/top-categories", tags=["Dashboard"])
async def get_top_categories(limit: int = 10, db: Session = Depends(get_db)):
    cats = db.query(
        Product.category,
        func.count(Product.id).label("count"),
        func.avg(Product.price).label("avg_price")
    ).filter(
        Product.category.isnot(None)
    ).group_by(Product.category).order_by(desc("count")).limit(limit).all()
    
    return [{"category": c, "count": n, "avg_price": round(p, 3) if p else 0} for c, n, p in cats]


@app.get("/api/dashboard/price-distribution", tags=["Dashboard"])
async def get_price_distribution(db: Session = Depends(get_db)):
    ranges = [
        ("0-10 TND", 0, 10),
        ("10-25 TND", 10, 25),
        ("25-50 TND", 25, 50),
        ("50-100 TND", 50, 100),
        ("100-200 TND", 100, 200),
        ("200+ TND", 200, 99999),
    ]
    
    result = []
    for label, min_p, max_p in ranges:
        count = db.query(Product).filter(
            Product.price >= min_p,
            Product.price < max_p
        ).count()
        result.append({"range": label, "count": count})
    
    return result


@app.get("/api/dashboard/promotions", tags=["Dashboard"])
async def get_current_promotions(limit: int = 20, db: Session = Depends(get_db)):
    promos = db.query(Product).filter(
        Product.has_promotion == True,
        Product.discount_percent.isnot(None)
    ).order_by(desc(Product.discount_percent)).limit(limit).all()
    
    return [product_to_dict(p) for p in promos]


@app.get("/api/dashboard/price-evolution", tags=["Dashboard"])
async def get_price_evolution(days: int = 30, db: Session = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=days)
    history = db.query(
        func.date(PriceHistory.recorded_at).label("date"),
        Product.site,
        func.avg(PriceHistory.price).label("avg_price"),
        func.count(PriceHistory.id).label("count")
    ).join(Product).filter(
        PriceHistory.recorded_at >= since,
        PriceHistory.price.isnot(None)
    ).group_by(
        func.date(PriceHistory.recorded_at), Product.site
    ).order_by("date").all()
    
    return [{"date": str(h.date), "site": h.site, "avg_price": round(h.avg_price, 3), "count": h.count} for h in history]


# ==================== PRODUCTS ====================

@app.get("/api/products", tags=["Products"])
async def get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    site: Optional[str] = None,
    brand: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    has_promotion: Optional[bool] = None,
    in_stock: Optional[bool] = None,
    sort_by: Optional[str] = "updated_at",
    sort_order: Optional[str] = "desc",
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    
    if search:
        query = query.filter(or_(
            Product.name.ilike(f"%{search}%"),
            Product.brand.ilike(f"%{search}%"),
            Product.description.ilike(f"%{search}%"),
        ))
    if site:
        query = query.filter(Product.site == site)
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if has_promotion is not None:
        query = query.filter(Product.has_promotion == has_promotion)
    if in_stock is not None:
        query = query.filter(Product.in_stock == in_stock)
    
    total = query.count()
    
    # Sorting
    sort_col = getattr(Product, sort_by, Product.updated_at)
    if sort_order == "desc":
        query = query.order_by(desc(sort_col))
    else:
        query = query.order_by(sort_col)
    
    products = query.offset((page - 1) * limit).limit(limit).all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "products": [product_to_dict(p) for p in products]
    }


@app.get("/api/products/{product_id}", tags=["Products"])
async def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    d = product_to_dict(product)
    
    # Add price history
    history = db.query(PriceHistory).filter(
        PriceHistory.product_id == product_id
    ).order_by(desc(PriceHistory.recorded_at)).limit(30).all()
    
    d["price_history"] = [
        {"price": h.price, "old_price": h.old_price, "date": h.recorded_at.isoformat()}
        for h in history
    ]
    return d


@app.get("/api/products/filters/brands", tags=["Products"])
async def get_brands(db: Session = Depends(get_db)):
    brands = db.query(distinct(Product.brand)).filter(Product.brand.isnot(None)).order_by(Product.brand).all()
    return [b[0] for b in brands]


@app.get("/api/products/filters/categories", tags=["Products"])
async def get_categories(db: Session = Depends(get_db)):
    cats = db.query(distinct(Product.category)).filter(Product.category.isnot(None)).order_by(Product.category).all()
    return [c[0] for c in cats]


# ==================== BENCHMARK ====================

@app.get("/api/benchmark", tags=["Benchmark"])
async def get_benchmark(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    brand: Optional[str] = None,
    min_diff: Optional[float] = None,
    db: Session = Depends(get_db)
):
    query = db.query(BenchmarkSnapshot)
    
    if search:
        query = query.filter(BenchmarkSnapshot.product_name_normalized.ilike(f"%{search}%"))
    if brand:
        query = query.filter(BenchmarkSnapshot.brand.ilike(f"%{brand}%"))
    if min_diff is not None:
        query = query.filter(BenchmarkSnapshot.price_diff_percent >= min_diff)
    
    total = query.count()
    snapshots = query.order_by(desc(BenchmarkSnapshot.price_diff_percent)).offset((page-1)*limit).limit(limit).all()
    
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "data": [benchmark_to_dict(s) for s in snapshots]
    }


@app.post("/api/benchmark/refresh", tags=["Benchmark"])
async def refresh_benchmark(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(update_benchmark_snapshots, db)
    return {"message": "Benchmark refresh started"}


# ==================== SCRAPING ====================

@app.post("/api/scraping/start", tags=["Scraping"])
async def start_scraping(
    background_tasks: BackgroundTasks,
    sites: List[str] = Query(default=["parashop", "parafendri", "tunisiepara"]),
    db: Session = Depends(get_db)
):
    # Check no running job
    running = db.query(ScrapingJob).filter(
        ScrapingJob.status == ScrapingStatusEnum.RUNNING
    ).first()
    if running:
        return {"message": "A scraping job is already running", "job_id": running.job_id, "status": "already_running"}
    
    job_id = create_scraping_job(db, sites)
    background_tasks.add_task(run_scraping_job, db, sites, job_id)
    
    return {"job_id": job_id, "sites": sites, "status": "started"}


@app.get("/api/scraping/jobs", tags=["Scraping"])
async def get_scraping_jobs(limit: int = 20, db: Session = Depends(get_db)):
    jobs = db.query(ScrapingJob).order_by(desc(ScrapingJob.created_at)).limit(limit).all()
    return [job_to_dict(j) for j in jobs]


@app.get("/api/scraping/jobs/{job_id}", tags=["Scraping"])
async def get_scraping_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(ScrapingJob).filter(ScrapingJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_to_dict(job)


@app.get("/api/scraping/logs/{job_id}", tags=["Scraping"])
async def get_scraping_logs(job_id: str, limit: int = 100, db: Session = Depends(get_db)):
    logs = db.query(ScrapingLog).filter(
        ScrapingLog.job_id == job_id
    ).order_by(desc(ScrapingLog.created_at)).limit(limit).all()
    return [{"id": l.id, "site": l.site, "level": l.level, "message": l.message, "created_at": l.created_at.isoformat()} for l in logs]


@app.get("/api/scraping/status", tags=["Scraping"])
async def get_scraping_status(db: Session = Depends(get_db)):
    running = db.query(ScrapingJob).filter(ScrapingJob.status == ScrapingStatusEnum.RUNNING).first()
    last_completed = db.query(ScrapingJob).filter(
        ScrapingJob.status == ScrapingStatusEnum.COMPLETED
    ).order_by(desc(ScrapingJob.completed_at)).first()
    
    return {
        "is_running": running is not None,
        "current_job": job_to_dict(running) if running else None,
        "last_completed": job_to_dict(last_completed) if last_completed else None,
    }


# ==================== EXPORTS ====================

@app.get("/api/export/csv", tags=["Export"])
async def export_products_csv(
    site: Optional[str] = None,
    has_promotion: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if site:
        query = query.filter(Product.site == site)
    if has_promotion is not None:
        query = query.filter(Product.has_promotion == has_promotion)
    
    products = [product_to_dict(p) for p in query.all()]
    filepath = export_csv(products)
    return FileResponse(filepath, media_type="text/csv", filename=os.path.basename(filepath))


@app.get("/api/export/excel", tags=["Export"])
async def export_products_excel(
    site: Optional[str] = None,
    has_promotion: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if site:
        query = query.filter(Product.site == site)
    if has_promotion is not None:
        query = query.filter(Product.has_promotion == has_promotion)
    
    products = [product_to_dict(p) for p in query.all()]
    filepath = export_excel(products)
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=os.path.basename(filepath)
    )


@app.get("/api/export/pdf", tags=["Export"])
async def export_products_pdf(
    site: Optional[str] = None,
    has_promotion: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Product)
    if site:
        query = query.filter(Product.site == site)
    if has_promotion is not None:
        query = query.filter(Product.has_promotion == has_promotion)
    
    products = [product_to_dict(p) for p in query.all()]
    filepath = export_pdf(products)
    return FileResponse(filepath, media_type="application/pdf", filename=os.path.basename(filepath))


@app.get("/api/export/benchmark/excel", tags=["Export"])
async def export_benchmark_excel_endpoint(db: Session = Depends(get_db)):
    snapshots = db.query(BenchmarkSnapshot).all()
    data = [benchmark_to_dict(s) for s in snapshots]
    filepath = export_benchmark_excel(data)
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=os.path.basename(filepath)
    )


# ==================== HEALTH ====================

@app.get("/api/health", tags=["System"])
async def health_check(db: Session = Depends(get_db)):
    product_count = db.query(Product).count()
    return {
        "status": "healthy",
        "version": "1.0.0",
        "products": product_count,
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== HELPERS ====================

def product_to_dict(p: Product) -> dict:
    return {
        "id": p.id,
        "site": p.site,
        "name": p.name,
        "brand": p.brand,
        "category": p.category,
        "subcategory": p.subcategory,
        "price": p.price,
        "old_price": p.old_price,
        "discount_percent": p.discount_percent,
        "has_promotion": p.has_promotion,
        "in_stock": p.in_stock,
        "image_url": p.image_url,
        "product_url": p.product_url,
        "description": p.description,
        "ean": p.ean,
        "last_scraped": p.last_scraped.isoformat() if p.last_scraped else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


def benchmark_to_dict(s: BenchmarkSnapshot) -> dict:
    return {
        "id": s.id,
        "product_name_normalized": s.product_name_normalized,
        "brand": s.brand,
        "price_parashop": s.price_parashop,
        "price_parafendri": s.price_parafendri,
        "price_tunisiepara": s.price_tunisiepara,
        "url_parashop": s.url_parashop,
        "url_parafendri": s.url_parafendri,
        "url_tunisiepara": s.url_tunisiepara,
        "min_price": s.min_price,
        "max_price": s.max_price,
        "price_diff_percent": s.price_diff_percent,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


def job_to_dict(j: ScrapingJob) -> dict:
    return {
        "id": j.id,
        "job_id": j.job_id,
        "sites": j.sites,
        "status": j.status,
        "total_products": j.total_products,
        "scraped_products": j.scraped_products,
        "new_products": j.new_products,
        "updated_products": j.updated_products,
        "failed_products": j.failed_products,
        "started_at": j.started_at.isoformat() if j.started_at else None,
        "completed_at": j.completed_at.isoformat() if j.completed_at else None,
        "created_at": j.created_at.isoformat() if j.created_at else None,
        "error_message": j.error_message,
    }
