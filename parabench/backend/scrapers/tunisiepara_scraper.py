import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper


class TunisieParaScraper(BaseScraper):
    site_name = "tunisiepara"
    base_url = "https://www.tunisiepara.com"

    async def scrape_categories(self) -> List[Dict]:
        categories = []
        content = await self.safe_get_page(self._context, self.base_url)
        if not content:
            return []
        soup = BeautifulSoup(content, "lxml")
        for link in soup.select("nav a, .categories a, .menu a"):
            href = link.get("href", "")
            text = link.get_text(strip=True)
            if href and text and "tunisiepara.com" in href:
                categories.append({"name": text, "url": href})
        return categories

    async def scrape_category_page(self, url: str, category: str, subcategory: str = "") -> List[Dict]:
        products = []
        page_num = 1
        
        while True:
            page_url = url
            if page_num > 1:
                sep = "&" if "?" in url else "?"
                page_url = f"{url}{sep}p={page_num}"
            
            self.log("INFO", f"Scraping {category} p.{page_num}")
            content = await self.safe_get_page(self._context, page_url)
            if not content:
                break
            
            soup = BeautifulSoup(content, "lxml")
            
            # PrestaShop / custom selectors
            cards = (
                soup.select(".product-miniature") or
                soup.select("li.ajax_block_product") or
                soup.select(".product-item-wrapper") or
                soup.select(".product_item") or
                soup.select(".product-container") or
                soup.select("article.product") or
                soup.select(".grid-item.product")
            )
            
            if not cards:
                self.log("WARNING", f"No product cards found on {page_url}")
                break
            
            page_products = []
            for card in cards:
                product = self._parse_product_card(card, category, subcategory)
                if product:
                    page_products.append(product)
            
            if not page_products:
                break
            
            products.extend(page_products)
            self.log("INFO", f"Page {page_num}: {len(page_products)} products")
            
            # Check next page - various patterns
            next_link = (
                soup.select_one("a[rel='next']") or
                soup.select_one(".pagination a.next") or
                soup.select_one("li.next a") or
                soup.select_one('[aria-label="Page suivante"]') or
                soup.select_one(".next-page a")
            )
            if not next_link:
                break
            
            page_num += 1
            if page_num > 60:
                break
            
            await self.random_delay()
        
        return products

    def _parse_product_card(self, card, category: str, subcategory: str) -> Optional[Dict]:
        try:
            # Product name
            name_el = (
                card.select_one(".product-title") or
                card.select_one(".product_name") or
                card.select_one("h2.product-title") or
                card.select_one("h3 a") or
                card.select_one("h2 a") or
                card.select_one(".item-name a") or
                card.select_one("a.product-name")
            )
            if not name_el:
                return None
            
            name = name_el.get_text(strip=True)
            if not name:
                return None
            
            # URL
            link_el = (
                name_el if name_el.name == "a" else name_el.find("a") or
                card.select_one("a.product_img_link") or
                card.select_one("a")
            )
            product_url = ""
            if link_el and link_el.name == "a":
                product_url = link_el.get("href", "")
            elif hasattr(link_el, 'get'):
                product_url = link_el.get("href", "")
            
            if not product_url:
                return None
            if not product_url.startswith("http"):
                product_url = self.base_url + product_url

            # Price handling
            price = None
            old_price = None
            
            # Current price
            for price_sel in [
                ".product-price-and-shipping .price",
                ".current-price .price",
                "span.price",
                ".product-price",
                "[class*='current-price']",
                ".price-box .price",
                ".our_price_display"
            ]:
                el = card.select_one(price_sel)
                if el:
                    price = self.parse_price(el.get_text(strip=True))
                    if price:
                        break
            
            # Old price
            for old_sel in [
                ".regular-price",
                ".old-price",
                "s.price",
                "del",
                ".price-old",
                ".crossed-out-price",
                ".old_price"
            ]:
                el = card.select_one(old_sel)
                if el:
                    old_price = self.parse_price(el.get_text(strip=True))
                    if old_price:
                        break

            # Brand
            brand_el = (
                card.select_one(".product-manufacturer img") or
                card.select_one(".brand-name") or
                card.select_one("[class*='brand']") or
                card.select_one(".manufacturer-name")
            )
            brand = None
            if brand_el:
                if brand_el.name == "img":
                    brand = brand_el.get("alt", "")
                else:
                    brand = brand_el.get_text(strip=True)

            # Image
            img_el = card.select_one("img.product_img_link, img.lazyload, img.lazy, img")
            image_url = None
            if img_el:
                image_url = (
                    img_el.get("data-src") or
                    img_el.get("data-original") or
                    img_el.get("data-lazy") or
                    img_el.get("src")
                )

            # Promotion
            promo_el = (
                card.select_one(".discount-badge") or
                card.select_one("[class*='discount']") or
                card.select_one(".badge-sale") or
                card.select_one("[class*='promo']") or
                card.select_one(".flag-discount")
            )
            has_promotion = promo_el is not None or (old_price and price and old_price > price)
            
            discount_percent = None
            if has_promotion and old_price and price and old_price > 0:
                discount_percent = round((old_price - price) / old_price * 100, 1)
            
            # Stock
            out_stock = (
                card.select_one("[class*='out-of-stock']") or
                card.select_one(".unavailable") or
                card.select_one("[class*='no-stock']")
            )
            in_stock = out_stock is None

            return {
                "site": "tunisiepara",
                "name": name,
                "brand": brand,
                "category": category,
                "subcategory": subcategory,
                "price": price,
                "old_price": old_price,
                "discount_percent": discount_percent,
                "has_promotion": has_promotion,
                "image_url": image_url,
                "product_url": product_url,
                "in_stock": in_stock,
                "description": None,
                "ean": None,
                "ingredients": None,
            }
        except Exception as e:
            self.log("WARNING", f"Parse error: {str(e)[:80]}")
            return None

    async def scrape_all_products(self) -> List[Dict]:
        all_products = []
        
        category_urls = [
            ("Visage", f"{self.base_url}/59-soin-visage"),
            ("Corps", f"{self.base_url}/60-soin-corps"),
            ("Cheveux", f"{self.base_url}/61-soin-cheveux"),
            ("Maquillage", f"{self.base_url}/62-maquillage"),
            ("Parfums", f"{self.base_url}/63-parfum"),
            ("Bébé", f"{self.base_url}/64-bebe"),
            ("Santé", f"{self.base_url}/65-sante"),
            ("Solaires", f"{self.base_url}/66-solaire"),
            ("Hygiène", f"{self.base_url}/67-hygiene"),
            ("Minceur", f"{self.base_url}/68-minceur"),
        ]
        
        # Dynamic discovery
        try:
            content = await self.safe_get_page(self._context, self.base_url)
            if content:
                soup = BeautifulSoup(content, "lxml")
                discovered = []
                for sel in ["#block_top_menu a", ".sf-menu a", "#main-nav a", ".nav-categories a", "nav a"]:
                    links = soup.select(sel)
                    if len(links) > 3:
                        for link in links:
                            href = link.get("href", "")
                            text = link.get_text(strip=True)
                            if href and text and len(text) > 2 and "tunisiepara.com" in href:
                                if any(c.isdigit() for c in href):
                                    discovered.append((text, href))
                        if discovered:
                            self.log("INFO", f"Discovered {len(discovered)} categories")
                            category_urls = list(dict.fromkeys([(t, u) for t, u in discovered]))[:20]
                            break
        except Exception as e:
            self.log("WARNING", f"Dynamic discovery failed: {e}")
        
        for cat_name, cat_url in category_urls:
            try:
                prods = await self.scrape_category_page(cat_url, cat_name)
                all_products.extend(prods)
                self.log("INFO", f"{cat_name}: {len(prods)} products")
                await self.random_delay()
            except Exception as e:
                self.log("ERROR", f"Error in {cat_name}: {e}")
        
        # Deduplicate
        seen = set()
        unique = []
        for p in all_products:
            if p["product_url"] not in seen:
                seen.add(p["product_url"])
                unique.append(p)
        
        self.log("INFO", f"Total unique TunisiePara products: {len(unique)}")
        return unique
