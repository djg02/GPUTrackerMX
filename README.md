# GPU Price Tracker
Aggregates and normalizes GPU listings from Mexican PC hardware retailers for price tracking, stock monitoring, and cross-store comparison.

## Features
- Scrapes GPU listings from multiple retailers
- Stores raw listing data in PostgreSQL
- Preserves full raw JSON payloads for reparsing and debugging
- Tracks pricing, stock status, shipping cost, and listing metadata
- Supports both API-based and browser-automation scraping workflows
- Parses and normalizes hardware attributes into structured fields

## Supported Stores
- DDTech
- Cyberpuerta
Additional retailers planned.

## Database Stores
Each listing stores:
- Store metadata
- Current price
- Stock availability
- Shipping cost
- Raw API responses
- Timestamps for updates and last seen activity

## Tech Stack
- Python
- PostgreSQL
- Playwright
- httpx
- psycopg

## Current Focus
- Building product normalization pipelines
- Expanding retailer coverage
- Developing cross-store GPU matching logic
- Preparing historical price tracking infrastructure

## Planned Features
- Canonical product matching across stores
- Historical price analytics
- REST API
- Frontend dashboard with price comparison
- Automated scheduled scraping
- CPU and other hardware category expansion
- Public web interface
