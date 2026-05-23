from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ProductSchema(BaseModel):
    id: int
    site: str
    name: str
    brand: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]
    price: Optional[float]
    old_price: Optional[float]
    discount_percent: Optional[float]
    has_promotion: bool
    in_stock: bool
    image_url: Optional[str]
    product_url: str

    class Config:
        from_attributes = True


class ScrapingStartRequest(BaseModel):
    sites: List[str] = ["parashop", "parafendri", "tunisiepara"]
