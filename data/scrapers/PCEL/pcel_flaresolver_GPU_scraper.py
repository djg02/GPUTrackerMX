from rich import print
from dotenv import load_dotenv
import psycopg
import os
import json
import re
import requests
import time

load_dotenv()

SKIP_KEYWORDS = [
    "soporte", "kit de montaje", "kit de soporte", "cable de extensión",
    "cable extensión", "cable strimer", "strimer", "riser",
]
GPU_KEYWORDS = [
    "nvidia", "radeon", "geforce", "radeon", "rtx", "gtx", "rx ", "arc a", "arc b", "quadro",
]

def is_actual_gpu(title):
    if not title:
        return False
    title_lower = title.lower()
    if any(kw in title_lower for kw in SKIP_KEYWORDS):
        return False
    if not any(kw in title_lower for kw in GPU_KEYWORDS):
        return False
    return True

FLARESOLVERR_URL = "http://flaresolverr:8191/v1"
BASE_LIST_URL = "https://www.pcel.com/hardware/tarjetas-de-video?sucursal=0&show_oos=1&page={page}"
STORE_ID = 4  # PCEL


def fs_create_session(session_id="pcel_session"):
    payload = {"cmd": "sessions.create", "session": session_id}
    r = requests.post(FLARESOLVERR_URL, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()


def fs_destroy_session(session_id="pcel_session"):
    payload = {"cmd": "sessions.destroy", "session": session_id}
    try:
        requests.post(FLARESOLVERR_URL, json=payload, timeout=30)
    except Exception:
        pass


def fs_get(url, session_id="pcel_session", max_timeout=60000):
    payload = {
        "cmd": "request.get",
        "url": url,
        "session": session_id,
        "maxTimeout": max_timeout,
    }
    r = requests.post(FLARESOLVERR_URL, json=payload, timeout=(max_timeout / 1000) + 10)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "ok":
        raise RuntimeError(f"FlareSolverr error: {data.get('message')}")
    return data["solution"]["response"]


def extract_listing_json(html):
    match = re.search(r'window\.PCEL_SEARCH\s*=\s*(\[.*?\]);', html, re.S)
    if not match:
        return None
    return json.loads(match.group(1))


def save_listing(cursor, conn, listing):
    cursor.execute(
        """
        INSERT INTO listing (
            StoreListingId, StoreId, StoreTitle, Link,
            AvailabilityStatus, CreatedAt, UpdatedAt, LastSeenAt,
            CurrentPrice, CurrentPriceUpdatedAt, ImageUrl,
            RawJson, Currency, ShippingPrice
        )
        VALUES (
            %s, %s, %s, %s,
            %s, NOW(), NOW(), NOW(),
            %s, NOW(), %s,
            %s, %s, %s
        )
        ON CONFLICT (StoreId, StoreListingId)
        DO UPDATE SET
            CurrentPrice = EXCLUDED.CurrentPrice,
            AvailabilityStatus = EXCLUDED.AvailabilityStatus,
            LastSeenAt = NOW(),
            RawJson = EXCLUDED.RawJson,
            UpdatedAt = NOW(),
            ImageUrl = EXCLUDED.ImageUrl,
            Currency = EXCLUDED.Currency,
            ShippingPrice = EXCLUDED.ShippingPrice
        RETURNING listingid;
        """,
        (
            listing["storelistingid"],
            listing["storeid"],
            listing["title"],
            listing["url"],
            listing["availability"],
            listing["price"],
            listing["imageurl"],
            json.dumps(listing["rawjson"]),
            listing["currency"],
            listing["shippingprice"],
        )
    )

    listingid = cursor.fetchone()[0]

    cursor.execute(
        """
        INSERT INTO pricesnapshot (listingid, currency, price, capturedat, shippingprice)
        VALUES (%s, %s, %s, NOW(), %s);
        """,
        (listingid, listing["currency"], listing["price"], listing["shippingprice"])
    )
    conn.commit()


def map_stock_status(product):
    # PCEL marks availability mostly through can_buy / stock_status_id
    if product.get("can_buy") is False:
        return "OutOfStock"
    return "InStock"


def run():
    conn = psycopg.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )
    cursor = conn.cursor()

    session_id = "pcel_session"
    fs_create_session(session_id)

    page_num = 1
    total_saved = 0

    try:
        while True:
            url = BASE_LIST_URL.format(page=page_num)
            print(f"[blue]Fetching page {page_num}:[/blue] {url}")

            try:
                html = fs_get(url, session_id=session_id)
            except Exception as e:
                print(f"[red]FlareSolverr request failed on page {page_num}:[/red] {e}")
                break

            products = extract_listing_json(html)

            if not products:
                print(f"[cyan]No products found on page {page_num}, stopping.[/cyan]")
                break

            print(f"[cyan]Found {len(products)} products on page {page_num}[/cyan]")

            for product in products:
                try:
                    title = product.get("name") or product.get("title")

                    if not is_actual_gpu(title):
                        print(f"[yellow]Skipping non-GPU listing:[/yellow] {title}")
                        continue

                    price = product.get("effective_price_raw") or product.get("price_raw")

                    listing = {
                        "storelistingid": str(product.get("id")),
                        "storeid": STORE_ID,
                        "title": title,
                        "url": product.get("href"),
                        "availability": map_stock_status(product),
                        "price": price,
                        "currency": "MXN",
                        "imageurl": product.get("thumb"),
                        "shippingprice": 0 if product.get("free_shipping") else None,
                        "rawjson": product,
                    }

                    save_listing(cursor, conn, listing)
                    total_saved += 1
                    print(f"[green]Saved:[/green] {title} | ${price}")

                except Exception as e:
                    print(f"[red]Failed to save listing:[/red] {product.get('title')}\n{e}")
                    conn.rollback()

            page_num += 1
            time.sleep(1.5)  # be polite between listing pages

    finally:
        fs_destroy_session(session_id)
        cursor.close()
        conn.close()

    print(f"[green]Finished. Total listings saved: {total_saved}[/green]")


if __name__ == "__main__":
    run()