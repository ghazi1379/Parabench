#!/usr/bin/env python3
"""
Script de test des scrapers — sans base de données
Usage: python3 scripts/test_scrapers.py [site]
  site: parashop | parafendri | tunisiepara | all (defaut: all)
"""
import asyncio
import sys
import json
from datetime import datetime

sys.path.insert(0, "backend")

from scrapers import SCRAPERS


async def test_scraper(site_name: str):
    print(f"\n{'='*60}")
    print(f"  Test scraper: {site_name.upper()}")
    print(f"{'='*60}")

    scraper_class = SCRAPERS.get(site_name)
    if not scraper_class:
        print(f"Scraper inconnu: {site_name}")
        return []

    def log_cb(job_id, site, level, msg):
        time = datetime.now().strftime("%H:%M:%S")
        color = {"INFO": "\033[94m", "ERROR": "\033[91m", "WARNING": "\033[93m"}.get(level, "")
        print(f"  {color}[{time}][{site}][{level}] {msg}\033[0m")

    scraper = scraper_class(job_id="test", log_callback=log_cb)

    start = datetime.now()
    products = await scraper.run()
    elapsed = (datetime.now() - start).total_seconds()

    print(f"\n📊 Résultats {site_name}:")
    print(f"   Produits scraped  : {len(products)}")
    print(f"   Durée             : {elapsed:.1f}s")

    if products:
        with_price = [p for p in products if p.get("price")]
        with_brand = [p for p in products if p.get("brand")]
        with_promo = [p for p in products if p.get("has_promotion")]

        print(f"   Avec prix         : {len(with_price)} ({len(with_price)/len(products)*100:.0f}%)")
        print(f"   Avec marque       : {len(with_brand)} ({len(with_brand)/len(products)*100:.0f}%)")
        print(f"   En promotion      : {len(with_promo)}")

        prices = [p["price"] for p in products if p.get("price")]
        if prices:
            print(f"   Prix min          : {min(prices):.3f} TND")
            print(f"   Prix max          : {max(prices):.3f} TND")
            print(f"   Prix moyen        : {sum(prices)/len(prices):.3f} TND")

        # Catégories
        cats = {}
        for p in products:
            cat = p.get("category", "N/A") or "N/A"
            cats[cat] = cats.get(cat, 0) + 1
        print(f"\n   Catégories: {len(cats)}")
        for cat, cnt in sorted(cats.items(), key=lambda x: -x[1])[:5]:
            print(f"     - {cat}: {cnt} produits")

        # Exemple produit
        print(f"\n   Exemple produit:")
        p = products[0]
        for k, v in p.items():
            if v and k != "description" and k != "ingredients":
                print(f"     {k}: {str(v)[:80]}")

        # Sauvegarde JSON (optionnel)
        output_file = f"/tmp/parabench_{site_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(products[:20], f, ensure_ascii=False, indent=2, default=str)
        print(f"\n   📄 Extrait sauvé : {output_file}")

    return products


async def main():
    site = sys.argv[1] if len(sys.argv) > 1 else "all"

    if site == "all":
        sites = list(SCRAPERS.keys())
    else:
        sites = [site]

    total_products = 0
    for site_name in sites:
        products = await test_scraper(site_name)
        total_products += len(products)

    print(f"\n{'='*60}")
    print(f"  TOTAL : {total_products} produits scraped")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
