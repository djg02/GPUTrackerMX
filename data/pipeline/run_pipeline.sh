#!/bin/bash
set -e

find /app/logs -name "*.log" -mtime +7 -delete

echo "=== Starting GPU Tracker Pipeline ==="

echo "-- Scrapers --"
python scrapers/Cyberpuerta/cyberpuerta_API_GPU_scraper.py
python scrapers/DDTech/ddtech_bs_flareresolver_GPU_scraper.py
python scrapers/DIGITALIFE/digitalife_API_GPU_scraper.py
python scrapers/Intercompras/intercompras_bs_flareresolver_GPU_scraper.py
python scrapers/PCEL/pcel_flaresolver_GPU_scraper.py
python scrapers/Zegucom/zegucom_bs_flareresolver_GPU_scraper.py
python scrapers/MercadoLibre/ML_camoufox_GPU_scraper.py
python scrapers/Amazon/Amazon_Playwright_GPU_scraper.py

echo "-- Parsers --"
python parsers/cyberpuerta_listing_parser.py
python parsers/DDTech_listing_parser.py
python parsers/digitalife_listing_parser.py
python parsers/intercompras_listing_parser.py
python parsers/pcel_listing_parser.py
python parsers/zegucom_listing_parser.py
python parsers/ML_listing_parser_scratch.py
python parsers/Amazon_listing_parser.py

echo "-- Normalize --"
python normalization/normalize_listings.py

echo "-- Round 1 --"
python matchers/match_by_sku.py
python matchers/match_by_specs.py
python matchers/match_by_sku.py

echo "-- Cyberpuerta to Product --"
python matchers/cyberpuerta_to_product.py
python matchers/match_by_sku.py
python matchers/match_by_specs.py
python matchers/match_by_sku.py

echo "-- Digitalife to Product --"
python matchers/digitalife_to_product.py
python matchers/match_by_sku.py
python matchers/match_by_specs.py
python matchers/match_by_sku.py

echo "-- Listing to Product --"
python matchers/listing_to_product.py
python matchers/match_by_sku.py
python matchers/match_by_specs.py
python matchers/match_by_sku.py

echo "-- Mark Stale Listings --"
python pipeline/mark_stale_listings.py

echo "=== Pipeline Complete ==="