# GPU Price Tracker

Aggregates and normalizes GPU listings from Mexican PC hardware retailers for price tracking, stock monitoring, and cross-store comparison.

## Features

* Scrapes GPU listings from multiple retailers
* Stores raw listing data in PostgreSQL
* Preserves full raw JSON payloads for reparsing and debugging
* Tracks pricing, stock status, shipping cost, and listing metadata
* Supports both API-based and browser-automation scraping workflows
* Parses and normalizes hardware attributes into structured fields
* Matches products across stores using specification-based and SKU-based matching
* Exposes product and listing data through a REST API
* Frontend dashboard for searching, filtering, and comparing GPU prices with historical price analytics

## Architecture

![GPU Tracker File Pipeline](assets/tracker_file_flowchart.drawio.png)

## Supported Stores

* MercadoLibre
* DDTech
* Cyberpuerta
* Digitalife
* PCEL
* Zegucom
* Additional retailers planned.

## API Documentation

See [`API/README.md`](./API/README.md) for endpoint details, query parameters, and response formats.

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
* TypeScript
* Node.js
* Express
* React
* Vite
* Tailwind CSS
* BeautifulSoup
* FlareSolverr
* Camoufox
* httpx
* psycopg

## Current Focus

* Update frontend dashboard with filters and detail pages
* Expanding retailer coverage
* Preparing historical price tracking infrastructure

## Planned Features

* Automated scheduled scraping
* CPU and other hardware category expansion
* Public web interface

