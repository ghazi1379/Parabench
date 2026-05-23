import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from scrapers.base_scraper import BaseScraper


class ParafendriScraper(BaseScraper):
    site_name = "parafendri"
    base_url = "https://parafendri.tn"

    async def scrape_categories(self) -> List[Dict]:
        categories = []
        content = await self.safe_get_page(self._context, self.base_url)
        if not content:
            return []
        soup = BeautifulSoup(content, "lxml")
        nav_links = soup.select("nav a, .menu a, .categories a")
        for link in nav_links:
            href = link.get("href", "")
            text = link.get_text(strip=True)
            if href and text and "parafendri.tn" in href:
                categories.append({"name": text, "url": href})
        return categories

    async def scrape_category_page(self, url: str, category: str, subcategory: str = "") -> List[Dict]:
        products = []
        page_num = 1
        
        while True:
            page_url = url
            if page_num > 1:
                sep = "&" if "?" in url else "?"
                page_url = f"{url}{sep}page={page_num}"
            
            self.log("INFO", f"Scraping {category} p.{page_num}")
            content = await self.safe_get_page(self._context, page_url)
            if not content:
                break
            
            soup = BeautifulSoup(content, "lxml")
            
            # WooCommerce-style selectors (common in TN e-commerce)
            cards = (
                soup.select("li.product") or
                soup.select(".woocommerce-loop-product__link") or
                soup.select(".product-item") or
                soup.select("article.product") or
                soup.select(".product_item") or
                soup.select(".products-grid .product")
            )
            
            if not cards:
                break
            
            page_products = []
            for card in cards:
                product = self._parse_product_card(card, category, subcategory)
                if product:
                    page_products.append(product)
            
            if not page_products:
                break
            
            products.extend(page_products)
            
            # Next page detection
            has_next = (
                soup.select_one("a.next") or
                soup.select_one(".next-page") or
                soup.select_one('[aria-label="Next"]') or
                soup.select_one(".pagination li.next")
            )
            if not has_next:
                break
            
            page_num += 1
            if page_num > 50:
                break
            
            await self.random_delay()
        
        return products

    def _parse_product_card(self, card, category: str, subcategory: str) -> Optional[Dict]:
        try:
            # Name & URL (WooCommerce style)
            name_el = (
                card.select_one("h2.woocommerce-loop-product__title") or
                card.select_one(".product-title") or
                card.select_one("h3 a") or
                card.select_one("h2 a") or
                card.select_one(".product-name")
            )
            if not name_el:
                return None
            
            name = name_el.get_text(strip=True)
            
            # URL
            link_el = card.select_one("a") or card.find("a")
            product_url = ""
            if link_el:
                product_url = link_el.get("href", "")
                if not product_url.startswith("http"):
                    product_url = self.base_url + product_url
            
            if not product_url:
                return None

            # Prices
            price = None
            old_price = None
            
            # WooCommerce price structure
            price_wrapper = card.select_one(".price")
            if price_wrapper:
                # Sale price (current)
                sale_el = price_wrapper.select_one("ins .amount, ins, .woocommerce-Price-amount:last-child")
                old_el = price_wrapper.select_one("del .amount, del, .woocommerce-Price-amount:first-child")
                
                if sale_el and old_el:
                    price = self.parse_price(sale_el.get_text(strip=True))
                    old_price = self.parse_price(old_el.get_text(strip=True))
                else:
                    price_el = price_wrapper.select_one(".amount, .woocommerce-Price-amount")
                    if price_el:
                        price = self.parse_price(price_el.get_text(strip=True))
            
            if not price:
                # Fallback: look for any price
                for sel in [".price", "[class*='price']", ".cost"]:
                    el = card.select_one(sel)
                    if el:
                        price = self.parse_price(el.get_text(strip=True))
                        if price:
                            break

            # Brand - often in category badge or meta
            brand_el = (
                card.select_one(".brand") or
                card.select_one("[class*='brand']") or
                card.select_one(".manufacturer") or
                card.select_one(".product-brand")
            )
            brand = brand_el.get_text(strip=True) if brand_el else None

            # Image
            img_el = card.select_one("img")
            image_url = None
            if img_el:
                image_url = (
                    img_el.get("data-src") or
                    img_el.get("data-lazy-src") or
                    img_el.get("src")
                )

            # Promotion
            promo_el = (
                card.select_one(".onsale") or
                card.select_one("[class*='sale']") or
                card.select_one("[class*='promo']") or
                card.select_one(".badge")
            )
            has_promotion = promo_el is not None or (old_price and price and old_price > price)
            
            discount_percent = None
            if has_promotion and old_price and price and old_price > 0:
                discount_percent = round((old_price - price) / old_price * 100, 1)

            # Stock
            out_stock = card.select_one(".out-of-stock, [class*='outofstock'], .unavailable")
            in_stock = out_stock is None

            return {
                "site": "parafendri",
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
            ("Soins du visage", f"{self.base_url}/categorie/soins-du-visage/"),
            ("Soins du corps", f"{self.base_url}/categorie/soins-du-corps/"),
            ("Soins cheveux", f"{self.base_url}/categorie/soins-cheveux/"),
            ("Maquillage", f"{self.base_url}/categorie/maquillage/"),
            ("Parfums", f"{self.base_url}/categorie/parfums/"),
            ("Bébé & Maman", f"{self.base_url}/categorie/bebe-maman/"),
            ("Santé", f"{self.base_url}/categorie/sante/"),
            ("Solaires", f"{self.base_url}/categorie/solaires/"),
            ("Hygiène", f"{self.base_url}/categorie/hygiene/"),
            ("Compléments", f"{self.base_url}/categorie/complements-alimentaires/"),
        ]
        
        # Try dynamic category discovery first
        try:
            content = await self.safe_get_page(self._context, self.base_url)
            if content:
                soup = BeautifulSoup(content, "lxml")
                discovered = []
                for sel in [".menu-item a", ".nav-menu a", ".main-navigation a", "nav ul li a"]:
                    links = soup.select(sel)
                    if len(links) > 3:
                        for link in links:
                            href = link.get("href", "")
                            text = link.get_text(strip=True)
                            if href and text and len(text) > 2 and "parafendri.tn" in href:
                                if "/categorie/" in href or "/category/" in href or "/shop/" in href:
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
                self.log("ERROR", f"Error in category {cat_name}: {e}")
        
        # Deduplicate
        seen = set()
        unique = []
        for p in all_products:
            if p["product_url"] not in seen:
                seen.add(p["product_url"])
                unique.append(p)
        
        self.log("INFO", f"Total unique Parafendri products: {len(unique)}")
        return unique
