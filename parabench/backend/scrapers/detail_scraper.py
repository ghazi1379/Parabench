"""
Scraper de pages produit individuelles
Récupère: description, EAN, ingrédients, stock précis
"""
import asyncio
import re
from typing import Optional, Dict
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from scrapers.base_scraper import BaseScraper


class ProductDetailScraper(BaseScraper):
    """Enrichit les données produit en visitant chaque page produit"""

    site_name = "detail"
    base_url = ""

    async def scrape_product_detail(self, url: str, site: str) -> Dict:
        """Scrape une page produit et retourne les champs enrichis"""
        content = await self.safe_get_page(self._context, url)
        if not content:
            return {}

        soup = BeautifulSoup(content, "lxml")
        result = {}

        # ---- Description ----
        desc_selectors = [
            "#description", ".product-description", ".description",
            "[itemprop='description']", ".product-details__description",
            ".woocommerce-product-details__short-description",
            ".product_description", "#tab-description",
        ]
        for sel in desc_selectors:
            el = soup.select_one(sel)
            if el:
                text = el.get_text(separator=" ", strip=True)
                if len(text) > 20:
                    result["description"] = text[:2000]
                    break

        # ---- EAN / BARCODE ----
        ean_patterns = [
            r'\b\d{13}\b',   # EAN-13
            r'\b\d{12}\b',   # UPC-A
        ]
        page_text = soup.get_text()
        for pattern in ean_patterns:
            ean_candidates = re.findall(pattern, page_text)
            for ean in ean_candidates:
                # Validate: EAN shouldn't be a price or date
                if not ean.startswith(('19', '20', '21', '22')):
                    result["ean"] = ean
                    break
            if "ean" in result:
                break

        # Look in specific EAN elements
        ean_el = soup.find(string=re.compile(r'EAN|Code.barre|Barcode', re.I))
        if ean_el and not result.get("ean"):
            parent = ean_el.parent
            if parent:
                eans = re.findall(r'\b\d{12,13}\b', parent.get_text())
                if eans:
                    result["ean"] = eans[0]

        # ---- Ingrédients ----
        ing_selectors = [
            "#ingredients", ".ingredients", "[class*='ingredient']",
            "#composition", ".composition", "[class*='composition']",
            "#tab-ingredients",
        ]
        for sel in ing_selectors:
            el = soup.select_one(sel)
            if el:
                text = el.get_text(separator=" ", strip=True)
                if len(text) > 10:
                    result["ingredients"] = text[:3000]
                    break

        # Fallback: look for "Ingrédients" section in text
        if not result.get("ingredients"):
            ing_label = soup.find(string=re.compile(r'ingr[eé]dients?|composition', re.I))
            if ing_label:
                parent = ing_label.find_parent(['div', 'section', 'p', 'td'])
                if parent:
                    text = parent.get_text(separator=" ", strip=True)
                    if len(text) > 20:
                        result["ingredients"] = text[:3000]

        # ---- Stock précis ----
        out_of_stock_signals = [
            soup.select_one(".out-of-stock"),
            soup.select_one("[class*='out-of-stock']"),
            soup.select_one(".unavailable"),
            soup.select_one("[class*='outofstock']"),
            soup.find(string=re.compile(r'rupture|indisponible|out of stock', re.I)),
        ]
        if any(out_of_stock_signals):
            result["in_stock"] = False
        else:
            in_stock_signals = [
                soup.select_one(".in-stock"),
                soup.select_one("[class*='in-stock']"),
                soup.select_one(".available"),
                soup.find(string=re.compile(r'en stock|disponible|in stock', re.I)),
            ]
            if any(in_stock_signals):
                result["in_stock"] = True

        # ---- Brand depuis microdata ----
        brand_el = soup.select_one("[itemprop='brand']")
        if brand_el:
            result["brand"] = brand_el.get_text(strip=True)

        return result

    async def enrich_products(self, products: list, max_detail: int = 50) -> list:
        """Enrichit une liste de produits avec les détails pages"""
        async with async_playwright() as playwright:
            browser, context = await self.get_browser(playwright)
            self._context = context
            try:
                enriched = []
                for i, product in enumerate(products):
                    if i >= max_detail:
                        enriched.append(product)
                        continue

                    self.log("INFO", f"Enriching {i+1}/{min(max_detail, len(products))}: {product['name'][:50]}")
                    detail = await self.scrape_product_detail(
                        product["product_url"], product["site"]
                    )
                    merged = {**product, **detail}
                    # Don't overwrite existing values with empty
                    for k, v in product.items():
                        if v and not merged.get(k):
                            merged[k] = v
                    enriched.append(merged)
                    await self.random_delay()

                return enriched
            finally:
                await context.close()
                await browser.close()

    async def scrape_all_products(self):
        return []

    async def scrape_categories(self):
        return []
