from rich import print
from dotenv import load_dotenv
import json
import os
import sys
import httpx
import psycopg
import time
import random
load_dotenv()

SEARCH_URL = "https://core.digitalife.com.mx/api/search/categoria_tarjetas-de-alto-desempeno"
PRODUCT_URL = "https://core.digitalife.com.mx/api/shop-v1/products/-actions/by-seo-part-number"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/vnd.api+json",
    "Accept-Language": "es-MX,es;q=0.9",
    "Origin": "https://www.digitalife.com.mx",
    "Referer": "https://www.digitalife.com.mx/",
    "Connection": "keep-alive",
}

store_id = 3

insert_query = """
    INSERT INTO listing (
        StoreListingId, StoreId, StoreTitle, Link, AvailabilityStatus,
        CreatedAt, UpdatedAt, LastseenAt, CurrentPrice, CurrentPriceUpdatedAt,
        ImageUrl, StockAmount, RawJson, Currency, ShippingPrice, SpecJson
    )
    VALUES (
        %s, %s, %s, %s, %s,
        NOW(), NOW(), NOW(), %s, NOW(),
        %s, %s, %s, %s, %s, %s
    )
    ON CONFLICT (StoreId, StoreListingId) DO UPDATE SET
        CurrentPrice = EXCLUDED.CurrentPrice,
        LastseenAt = NOW(),
        UpdatedAt = NOW(),
        StockAmount = EXCLUDED.StockAmount,
        AvailabilityStatus = EXCLUDED.AvailabilityStatus,
        ShippingPrice = EXCLUDED.ShippingPrice,
        RawJson = EXCLUDED.RawJson,
        SpecJson = EXCLUDED.SpecJson;
"""


def get_availability(stock_stores, stock_providers):
    if stock_stores > 0:
        return "InStock"
    elif stock_providers > 0:
        return "Available"
    else:
        return "OutOfStock"


conn = psycopg.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 5432)),
)
cursor = conn.cursor()

try:
    with httpx.Client(timeout=30, headers=headers, http2=True) as client:

        # Pass 1: get all products paginated
        page = 1
        per_page = 30
        all_products = []

        while True:
            try:
                response = client.get(SEARCH_URL, params={"per_page": per_page, "page": page})
                response.raise_for_status()
                data = response.json()
                products = data.get("data", [])

                if not products:
                    break

                all_products.extend(products)
                total = data.get("meta", {}).get("pagination", {}).get("total", 0)
                print(f"[cyan]Page {page}: got {len(products)} products (total so far: {len(all_products)}/{total})[/cyan]")

                if len(all_products) >= total:
                    break

                page += 1
                time.sleep(random.uniform(1.5, 3.0))

            except httpx.HTTPStatusError as e:
                print(f"[bold red]Failed on page {page}:[/bold red] {e.response.status_code}")
                break

        if not all_products:
            print("[bold red]No products found.[/bold red]")
            sys.exit(1)

        print(f"[cyan]Total products collected: {len(all_products)}[/cyan]")

        # Pass 2: enrich each product with full attribute_group_map
        for product in all_products:
            seo_part_number = product.get("seo_part_number")
            product_id = str(product.get("id"))

            if not seo_part_number:
                print(f"[yellow]Skipping {product_id} — no seo_part_number[/yellow]")
                continue

            time.sleep(random.uniform(0.8, 2.0))

            try:
                attr_response = client.get(f"{PRODUCT_URL}/{seo_part_number}")
                attr_response.raise_for_status()
                spec_json = attr_response.json().get("data", {}).get("attributes", {})

            except httpx.HTTPStatusError as e:
                print(f"[red]Failed fetching specs for {seo_part_number}:[/red] {e.response.status_code}")
                spec_json = None

            except Exception as e:
                print(f"[red]Failed fetching specs for {seo_part_number}:[/red] {e}")
                spec_json = None

            if spec_json is None:
                print(f"[yellow]Skipping DB write for {seo_part_number} — specs failed[/yellow]")
                continue

            stock_stores = product.get("stock_stores", 0) or 0
            stock_providers = product.get("stock_providers", 0) or 0
            cover = product.get("small_cover") or {}
            link = f"https://www.digitalife.com.mx/productos/{seo_part_number}/{product.get('slug', '')}"

            row = (
                product_id,
                store_id,
                product.get("name"),
                link,
                get_availability(stock_stores, stock_providers),
                product.get("current_price_with_tax"),
                cover.get("filename"),
                stock_stores + stock_providers,
                json.dumps(product, default=str),
                "MXN",
                0 if product.get("has_shipping_promotion") else None,
                json.dumps(spec_json, default=str),
            )

            try:
                cursor.execute(insert_query, row)
                conn.commit()
                print(f"[green]Saved {seo_part_number}[/green]")
            except Exception as db_err:
                conn.rollback()
                print(f"[red]DB error for {seo_part_number}:[/red] {db_err}")

finally:
    cursor.close()
    conn.close()

print("[bold green]Finished Scraping Loop Successfully[/bold green]")