-- ParaBench Database Initialization
-- PostgreSQL

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- The tables are created by SQLAlchemy on startup
-- This file can be used for additional setup

-- Create indexes for full-text search after tables exist
-- (These will be created by SQLAlchemy too via models)

-- Useful views
CREATE OR REPLACE VIEW v_products_summary AS
SELECT 
    site,
    COUNT(*) as total,
    COUNT(CASE WHEN has_promotion THEN 1 END) as with_promo,
    ROUND(AVG(price)::numeric, 3) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price
FROM products
WHERE price IS NOT NULL
GROUP BY site;

CREATE OR REPLACE VIEW v_brand_benchmark AS
SELECT 
    brand,
    COUNT(DISTINCT site) as sites_count,
    COUNT(*) as total_products,
    ROUND(AVG(price)::numeric, 3) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price
FROM products
WHERE brand IS NOT NULL AND price IS NOT NULL
GROUP BY brand
ORDER BY total_products DESC;

CREATE OR REPLACE VIEW v_category_stats AS
SELECT
    category,
    COUNT(*) as total_products,
    COUNT(DISTINCT brand) as brands_count,
    COUNT(DISTINCT site) as sites_count,
    ROUND(AVG(price)::numeric, 3) as avg_price
FROM products
WHERE category IS NOT NULL
GROUP BY category
ORDER BY total_products DESC;
