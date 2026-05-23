import asyncio
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from loguru import logger

from models.models import Product, PriceHistory, ScrapingJob, ScrapingLog, ScrapingStatusEnum, BenchmarkSnapshot
from scrapers import SCRAPERS


def create_log(db: Session, job_id: str, site: str, level: str, message: str):
    try:
        log = ScrapingLog(job_id=job_id, site=site, level=level, message=message)
        db.add(log)
        db.commit()
    except:
        db.rollback()


def upsert_product(db: Session, data: dict) -> tuple[bool, bool]:
    """Returns (is_new, is_updated)"""
    existing = db.query(Product).filter(
        Product.site == data["site"],
        Product.product_url == data["product_url"]
    ).first()
    
    if existing:
        # Track price history if price changed
        price_changed = existing.price != data.get("price")
        if price_changed:
            history = PriceHistory(
                product_id=existing.id,
                price=data.get("price"),
                old_price=data.get("old_price"),
                has_promotion=data.get("has_promotion", False)
            )
            db.add(history)
        
        # Update fields
        for key, value in data.items():
            if key != "site" and hasattr(existing, key):
                setattr(existing, key, value)
        existing.last_scraped = datetime.utcnow()
        db.commit()
        return False, price_changed
    else:
        product = Product(**{k: v for k, v in data.items() if hasattr(Product, k)})
        db.add(product)
        db.flush()
        
        # Initial price history
        if data.get("price"):
            history = PriceHistory(
                product_id=product.id,
                price=data.get("price"),
                old_price=data.get("old_price"),
                has_promotion=data.get("has_promotion", False)
            )
            db.add(history)
        db.commit()
        return True, False


async def run_scraping_job(db: Session, sites: List[str], job_id: str):
    job = db.query(ScrapingJob).filter(ScrapingJob.job_id == job_id).first()
    if not job:
        return
    
    job.status = ScrapingStatusEnum.RUNNING
    job.started_at = datetime.utcnow()
    db.commit()
    
    total_new = 0
    total_updated = 0
    total_failed = 0
    total_scraped = 0
    
    log_cb = lambda jid, site, level, msg: create_log(db, jid, site, level, msg)
    
    for site_name in sites:
        if site_name not in SCRAPERS:
            create_log(db, job_id, site_name, "ERROR", f"Unknown scraper: {site_name}")
            continue
        
        create_log(db, job_id, site_name, "INFO", f"Starting scraper for {site_name}")
        
        scraper_class = SCRAPERS[site_name]
        scraper = scraper_class(job_id=job_id, log_callback=log_cb)
        
        try:
            products = await scraper.run()
            create_log(db, job_id, site_name, "INFO", f"Scraped {len(products)} products from {site_name}")
            
            for product_data in products:
                try:
                    is_new, is_updated = upsert_product(db, product_data)
                    if is_new:
                        total_new += 1
                    elif is_updated:
                        total_updated += 1
                    total_scraped += 1
                except Exception as e:
                    total_failed += 1
                    logger.error(f"Error saving product: {e}")
            
            # Update job progress
            job.scraped_products = total_scraped
            job.new_products = total_new
            job.updated_products = total_updated
            job.failed_products = total_failed
            db.commit()
            
        except Exception as e:
            create_log(db, job_id, site_name, "ERROR", f"Scraper failed: {str(e)}")
    
    # Update benchmark after scraping
    try:
        await update_benchmark_snapshots(db)
        create_log(db, job_id, "system", "INFO", "Benchmark snapshots updated")
    except Exception as e:
        create_log(db, job_id, "system", "ERROR", f"Benchmark update failed: {e}")
    
    job.status = ScrapingStatusEnum.COMPLETED if total_failed == 0 else ScrapingStatusEnum.PARTIAL
    job.completed_at = datetime.utcnow()
    job.total_products = total_scraped
    db.commit()
    
    create_log(db, job_id, "system", "INFO", 
               f"Job completed. New: {total_new}, Updated: {total_updated}, Failed: {total_failed}")


async def update_benchmark_snapshots(db: Session):
    """Match products across sites by normalized name"""
    # Get all products grouped by normalized name
    products = db.query(Product).filter(Product.price.isnot(None)).all()
    
    grouped = {}
    for p in products:
        normalized = p.name.lower().strip()[:100]
        if normalized not in grouped:
            grouped[normalized] = {}
        grouped[normalized][p.site] = p
    
    # Update or create snapshots for products found on 2+ sites
    for norm_name, site_products in grouped.items():
        if len(site_products) < 2:
            continue
        
        snapshot = db.query(BenchmarkSnapshot).filter(
            BenchmarkSnapshot.product_name_normalized == norm_name
        ).first()
        
        prices = {site: p.price for site, p in site_products.items() if p.price}
        all_prices = list(prices.values())
        
        data = {
            "product_name_normalized": norm_name,
            "brand": next(iter(site_products.values())).brand,
            "price_parashop": prices.get("parashop"),
            "price_parafendri": prices.get("parafendri"),
            "price_tunisiepara": prices.get("tunisiepara"),
            "url_parashop": site_products.get("parashop", None) and site_products["parashop"].product_url,
            "url_parafendri": site_products.get("parafendri", None) and site_products["parafendri"].product_url,
            "url_tunisiepara": site_products.get("tunisiepara", None) and site_products["tunisiepara"].product_url,
            "min_price": min(all_prices) if all_prices else None,
            "max_price": max(all_prices) if all_prices else None,
            "price_diff_percent": round((max(all_prices) - min(all_prices)) / min(all_prices) * 100, 1) if len(all_prices) >= 2 and min(all_prices) > 0 else None,
        }
        
        if snapshot:
            for k, v in data.items():
                setattr(snapshot, k, v)
            snapshot.updated_at = datetime.utcnow()
        else:
            snapshot = BenchmarkSnapshot(**data)
            db.add(snapshot)
    
    db.commit()


def create_scraping_job(db: Session, sites: List[str]) -> str:
    job_id = str(uuid.uuid4())[:12]
    job = ScrapingJob(
        job_id=job_id,
        sites=",".join(sites),
        status=ScrapingStatusEnum.PENDING
    )
    db.add(job)
    db.commit()
    return job_id
