# GPU Price Tracker

Aggregates and normalizes GPU listings from Mexican PC hardware retailers for price tracking, stock monitoring, and cross-store comparison.

## Features

* Scrapes GPU listings from multiple retailers
* Stores raw listing data in PostgreSQL
* Preserves full raw JSON payloads for reparsing and debugging
* Tracks pricing, stock status, shipping cost, and listing metadata
* Supports both API-based and browser-automation scraping workflows
* Parses and normalizes hardware attributes into structured fields
* Matches products across stores using SKU-based matching

## Supported Stores

* DDTech
* Cyberpuerta
* Digitalife
* Additional retailers planned.

## Database Stores

Each listing stores:

* Store metadata
* Current price
* Stock availability
* Shipping cost
* Raw API responses
* Timestamps for updates and last seen activity

## Tech Stack

* Python
* PostgreSQL
* Playwright
* httpx
* psycopg

## Current Focus

* Improving product matching accuracy
* Developing specification-based matching
* Expanding retailer coverage
* Preparing historical price tracking infrastructure

## Planned Features

* Historical price analytics
* REST API
* Frontend dashboard with price comparison
* Automated scheduled scraping
* CPU and other hardware category expansion
* Public web interface

