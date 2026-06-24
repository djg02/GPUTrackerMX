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

FILTER_URL = "https://api.cyberpuerta.mx/v2/catalog/filter"
ARTICLES_URL = "https://api.cyberpuerta.mx/v2/catalog/articles"
ATTRIBUTES_URL = "https://api.cyberpuerta.mx/v2/pdp/articles" 
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.cyberpuerta.mx",
    "Referer": "https://www.cyberpuerta.mx/",
    "Connection": "keep-alive",
}

store_id = 2

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
        SpecJson = EXCLUDED.SpecJson
    RETURNING listingid, currentprice, shippingprice, currency;
"""

snapshot_query = """
    INSERT INTO pricesnapshot (listingid, currency, price, capturedat, shippingprice)
    VALUES (%s, %s, %s, NOW(), %s);
"""


def chunk_list(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


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

        try:
            response = client.get(FILTER_URL, params={
                "id": "30ee946749fd3e8fb8e6c3916e5d08e8",
                "type": "cat",
                "pageSize": 9999,
            })
            response.raise_for_status()
            data = response.json()
            article_ids = data.get("data", {}).get("articleIds", [])

            if not article_ids:
                print("[bold red]No article IDs returned — check the API response.[/bold red]")
                sys.exit(1)

            print(f"[cyan]found {len(article_ids)} article ids[/cyan]")

        except httpx.HTTPStatusError as e:
            print(f"[bold red]Critical initialization failure:[/bold red] {e.response.status_code} on initial filter.")
            sys.exit(1)

        for chunk in chunk_list(article_ids, 24):
            time.sleep(random.uniform(3, 6))
            try:
                time.sleep(random.uniform(0.7, 2.0))
                params = [("articles[]", article_id) for article_id in chunk]
                response = client.get(ARTICLES_URL, params=params)
                response.raise_for_status()
                products = response.json().get("data", [])

                if not products:
                    continue

                print(f"[yellow]Processing batch of {len(products)} products...[/yellow]")

                batch_data = []
                for product in products:
                    product_id = product.get("id")

                    try:
                        time.sleep(random.uniform(0.3, 1.0))
                        attr_response = client.get(f"{ATTRIBUTES_URL}/{product_id}/attributes")
                        attr_response.raise_for_status()
                        spec_json = attr_response.json().get("data", {})

                    except httpx.HTTPStatusError as e:
                        print(f"[red]Failed fetching specs for {product_id}:[/red] {e.response.status_code}")
                        spec_json = None

                    except Exception as attr_err:
                        print(f"[red]Failed fetching specs for {product_id}:[/red] {attr_err}")
                        spec_json = None
                    
                    if spec_json is None:
                        print(f"[yellow]Skipping DB write for {product_id} — specs failed[/yellow]")
                        continue


                    batch_data.append((
                        product.get("id"),
                        store_id,
                        product.get("title", "Unknown Title"),
                        product.get("link"),
                        product.get("availability"),
                        product.get("price"),
                        product.get("picture", "").replace("/img/product/S/", "/img/product/L/"),
                        product.get("stock"),
                        json.dumps(product, default=str),
                        "MXN",
                        product.get("shipping"),
                        json.dumps(spec_json, default=str),
                    ))

                try:
                    for row in batch_data:
                        cursor.execute(insert_query, row)
                        listingid, currentprice, shippingprice, currency = cursor.fetchone()
                        cursor.execute(snapshot_query, (listingid, currency, currentprice, shippingprice))
                    conn.commit()
                except Exception as db_err:
                    conn.rollback()
                    print(f"[red]DB error, batch rolled back:[/red] {db_err}")
                    continue

                print(f"[green]Successfully saved batch of {len(products)} products[/green]")

            except httpx.HTTPStatusError as e:
                print(f"[red]HTTP error on batch ({e.response.status_code}):[/red] {e.request.url}")
            except Exception as e:
                print(f"[red]Failed to process chunk:[/red] {e}")

finally:
    cursor.close()
    conn.close()

print("[bold green]Finished Scraping Loop Successfully[/bold green]")