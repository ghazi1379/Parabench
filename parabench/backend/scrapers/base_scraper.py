import asyncio
import random
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from bs4 import BeautifulSoup
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
import os

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
]


class BaseScraper(ABC):
    site_name: str = ""
    base_url: str = ""

    def __init__(self, job_id: str = "", log_callback=None):
        self.job_id = job_id
        self.log_callback = log_callback
        self.delay_min = float(os.getenv("SCRAPING_DELAY_MIN", 1.5))
        self.delay_max = float(os.getenv("SCRAPING_DELAY_MAX", 4.0))
        self.max_retries = int(os.getenv("MAX_RETRIES", 3))
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    def log(self, level: str, message: str):
        log_fn = getattr(logger, level.lower(), logger.info)
        log_fn(f"[{self.site_name}] {message}")
        if self.log_callback:
            self.log_callback(self.job_id, self.site_name, level, message)

    async def random_delay(self):
        delay = random.uniform(self.delay_min, self.delay_max)
        await asyncio.sleep(delay)

    async def get_browser(self, playwright):
        user_agent = random.choice(USER_AGENTS)
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",
            ]
        )
        context = await browser.new_context(
            user_agent=user_agent,
            viewport={"width": random.randint(1200, 1920), "height": random.randint(800, 1080)},
            locale="fr-TN",
            timezone_id="Africa/Tunis",
            extra_http_headers={
                "Accept-Language": "fr-TN,fr;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            }
        )
        # Block images and fonts to speed up
        await context.route("**/*.{png,jpg,jpeg,gif,webp,svg,ico,woff,woff2,ttf}", lambda route: route.abort())
        return browser, context

    async def safe_get_page(self, context: BrowserContext, url: str, wait_for: str = None) -> Optional[str]:
        page = None
        try:
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            if wait_for:
                try:
                    await page.wait_for_selector(wait_for, timeout=10000)
                except:
                    pass
            await self.random_delay()
            content = await page.content()
            return content
        except Exception as e:
            self.log("WARNING", f"Error loading {url}: {str(e)[:100]}")
            return None
        finally:
            if page:
                try:
                    await page.close()
                except:
                    pass

    def parse_price(self, price_str: str) -> Optional[float]:
        if not price_str:
            return None
        try:
            cleaned = price_str.replace("TND", "").replace("DT", "").replace("د.ت", "")
            cleaned = cleaned.replace(",", ".").replace(" ", "").replace("\xa0", "")
            cleaned = ''.join(c for c in cleaned if c.isdigit() or c == '.')
            if cleaned:
                return round(float(cleaned), 3)
        except:
            pass
        return None

    def normalize_name(self, name: str) -> str:
        if not name:
            return ""
        import re
        name = name.strip().lower()
        name = re.sub(r'\s+', ' ', name)
        return name

    @abstractmethod
    async def scrape_all_products(self) -> List[Dict]:
        pass

    @abstractmethod
    async def scrape_categories(self) -> List[Dict]:
        pass

    async def run(self) -> List[Dict]:
        products = []
        async with async_playwright() as playwright:
            browser, context = await self.get_browser(playwright)
            self._browser = browser
            self._context = context
            try:
                self.log("INFO", f"Starting scrape of {self.base_url}")
                products = await self.scrape_all_products()
                self.log("INFO", f"Scraped {len(products)} products from {self.site_name}")
            except Exception as e:
                self.log("ERROR", f"Fatal error during scraping: {str(e)}")
            finally:
                await context.close()
                await browser.close()
        return products
