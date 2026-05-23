from scrapers.parashop_scraper import ParashopScraper
from scrapers.parafendri_scraper import ParafendriScraper
from scrapers.tunisiepara_scraper import TunisieParaScraper

SCRAPERS = {
    "parashop": ParashopScraper,
    "parafendri": ParafendriScraper,
    "tunisiepara": TunisieParaScraper,
}

__all__ = ["ParashopScraper", "ParafendriScraper", "TunisieParaScraper", "SCRAPERS"]
