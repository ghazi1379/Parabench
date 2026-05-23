import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper


class ParashopScraper(BaseScraper):
    site_name = "parashop"
    base_url = "https://www.parashop.tn"

    async def scrape_categories(self) -> List[Dict]:
        categories = []
        content = await self.safe_get_page(self._context, self.base_url)
        if not content:
            return []
        soup = BeautifulSoup(content, "lxml")
        nav_links = soup.select("nav a, .menu a, .navbar a, ul.nav a")
        for link in nav_links:
            href = link.get("href", "")
            text = link.get_text(strip=True)
            if href and text and len(text) > 2:
                full_url = href if href.startswith("http") else self.base_url + href
                if "parashop.tn" in full_url:
                    categories.append({"name": text, "url": full_url})
        return categories

    async def scrape_category_page(self, url: str, category: str, subcategory: str = "") -> List[Dict]:
        products = []
        page_num = 1
        
        while True:
            page_url = url
            if page_num > 1:
                separator = "&" if "?" in url else "?"
                page_url = f"{url}{separator}page={page_num}"
            
            self.log("INFO", f"Scraping {category} page {page_num}: {page_url}")
            content = await self.safe_get_page(self._context, page_url)
            
            if not content:
                break
                
            soup = BeautifulSoup(content, "lxml")
            
            # Product cards - try multiple selectors
            product_cards = (
                soup.select(".product-item") or
                soup.select(".product_item") or
                soup.select("article.product") or
                soup.select(".product-miniature") or
                soup.select(".products .product") or
                soup.select("[data-product-id]") or
                soup.select(".card.product")
            )
            
            if not product_cards:
                # Try to find any product links
                product_cards = soup.select("li.ajax_block_product")
                if not product_cards:
                    break
            
            if not product_cards:
                break
                
            page_products = []
            for card in product_cards:
                product = await self._parse_product_card(card, category, subcategory)
                if product:
                    page_products.append(product)
            
            if not page_products:
                break
                
            products.extend(page_products)
            self.log("INFO", f"Found {len(page_products)} products on page {page_num}")
            
            # Check for next page
            next_link = soup.select_one("a[rel='next'], .next a, li.next a, .pagination .next")
            if not next_link:
                break
            
            page_num += 1
            if page_num > 50:  # Safety limit
                break
            
            await self.random_delay()
        
        return products

    async def _parse_product_card(self, card, category: str, subcategory: str) -> Optional[Dict]:
        try:
            # Name
            name_el = (
                card.select_one(".product-title a") or
                card.select_one("h3 a") or
                card.select_one("h2 a") or
                card.select_one(".product-name a") or
                card.select_one("a.product-name")
            )
            if not name_el:
                return None
            
            name = name_el.get_text(strip=True)
            product_url = name_el.get("href", "")
            if not product_url.startswith("http"):
                product_url = self.base_url + product_url

            # Price
            price_el = (
                card.select_one(".price") or
                card.select_one(".product-price") or
                card.select_one("[class*='price']")
            )
            price = None
            old_price = None
            
            if price_el:
                price_text = price_el.get_text(strip=True)
                prices = re.findall(r'[\d\s]+[,.]?\d*', price_text)
                if prices:
                    price = self.parse_price(prices[0])
            
            # Old price
            old_price_el = (
                card.select_one(".regular-price") or
                card.select_one(".old-price") or
                card.select_one("[class*='old-price']") or
                card.select_one("del")
            )
            if old_price_el:
                old_price = self.parse_price(old_price_el.get_text(strip=True))

            # Brand
            brand_el = (
                card.select_one(".product-manufacturer") or
                card.select_one(".brand") or
                card.select_one("[class*='brand']") or
                card.select_one(".manufacturer")
            )
            brand = brand_el.get_text(strip=True) if brand_el else None

            # Image
            img_el = card.select_one("img")
            image_url = None
            if img_el:
                image_url = (
                    img_el.get("data-src") or
                    img_el.get("data-lazy") or
                    img_el.get("src") or
                    img_el.get("data-original")
                )

            # Promotion
            promo_el = (
                card.select_one(".badge.sale") or
                card.select_one(".discount-badge") or
                card.select_one("[class*='promo']") or
                card.select_one("[class*='discount']") or
                card.select_one("[class*='sale']")
            )
            has_promotion = promo_el is not None or (old_price is not None and price is not None and old_price > price)
            
            discount_percent = None
            if has_promotion and old_price and price and old_price > 0:
                discount_percent = round((old_price - price) / old_price * 100, 1)

            # Stock
            out_of_stock = card.select_one("[class*='out-of-stock']") or card.select_one("[class*='unavailable']")
            in_stock = out_of_stock is None

            return {
                "site": "parashop",
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
            self.log("WARNING", f"Error parsing product card: {str(e)[:100]}")
            return None

    async def scrape_all_products(self) -> List[Dict]:
        all_products = []
        
        # Main category structure for parashop.tn
        category_urls = [
            ("Soins du visage", f"{self.base_url}/fr/39-soins-du-visage"),
            ("Soins du corps", f"{self.base_url}/fr/40-soins-du-corps"),
            ("Cheveux", f"{self.base_url}/fr/41-soins-cheveux"),
            ("Maquillage", f"{self.base_url}/fr/42-maquillage"),
            ("Parfums", f"{self.base_url}/fr/43-parfums"),
            ("Bébé & Maman", f"{self.base_url}/fr/44-bebe-maman"),
            ("Santé & Bien-être", f"{self.base_url}/fr/45-sante"),
            ("Solaires", f"{self.base_url}/fr/46-solaires"),
            ("Hygiène", f"{self.base_url}/fr/47-hygiene"),
            ("Nutrition", f"{self.base_url}/fr/48-nutrition"),
        ]
        
        # First, try to discover categories dynamically
        try:
            content = await self.safe_get_page(self._context, self.base_url)
            if content:
                soup = BeautifulSoup(content, "lxml")
                discovered = []
                
                # Try common menu structures
                for sel in ["#header .nav a", ".top-menu a", ".main-nav a", ".category-list a"]:
                    links = soup.select(sel)
                    if links:
                        for link in links:
                            href = link.get("href", "")
                            text = link.get_text(strip=True)
                            if href and text and len(text) > 2 and "parashop.tn" in href:
                                discovered.append((text, href))
                        if discovered:
                            self.log("INFO", f"Discovered {len(discovered)} categories dynamically")
                            category_urls = discovered[:20]
                            break
        except Exception as e:
            self.log("WARNING", f"Dynamic category discovery failed: {e}, using defaults")
        
        for category_name, category_url in category_urls:
            try:
                self.log("INFO", f"Processing category: {category_name}")
                products = await self.scrape_category_page(category_url, category_name)
                all_products.extend(products)
                self.log("INFO", f"Total from {category_name}: {len(products)} products")
                await self.random_delay()
            except Exception as e:
                self.log("ERROR", f"Error scraping category {category_name}: {str(e)}")
        
        # Deduplicate by URL
        seen_urls = set()
        unique_products = []
        for p in all_products:
            if p["product_url"] not in seen_urls:
                seen_urls.add(p["product_url"])
                unique_products.append(p)
        
        self.log("INFO", f"Total unique products from Parashop: {len(unique_products)}")
        return unique_products
