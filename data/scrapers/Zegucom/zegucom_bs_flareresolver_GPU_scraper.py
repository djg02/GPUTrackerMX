from rich import print
from dotenv import load_dotenv
from urllib.parse import urljoin
from collections import defaultdict
import psycopg
import os
import json
import requests
import time

load_dotenv()

FLARESOLVERR_URL = "http://flaresolverr:8191/v1"
BASE_URL = "https://www.zegucom.com.mx/Subcategorias/tarjetas-de-video-pci-exp/PCI/3"
JOIN_URL = "https://www.zegucom.com.mx/"
STORE_ID = 6


def fs_create_session(session_id="zegucom_session"):
    payload = {"cmd": "sessions.create", "session": session_id}
    r = requests.post(FLARESOLVERR_URL, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()


def fs_destroy_session(session_id="zegucom_session"):
    payload = {"cmd": "sessions.destroy", "session": session_id}
    try:
        requests.post(FLARESOLVERR_URL, json=payload, timeout=30)
    except Exception:
        pass


def fs_get(url, session_id="zegucom_session", max_timeout=60000):
    payload = {
        "cmd": "request.get",
        "url": url,
        "session": session_id,
        "maxTimeout": max_timeout,
    }

    r = requests.post(FLARESOLVERR_URL, json=payload, timeout=70)
    r.raise_for_status()

    data = r.json()
    if data.get("status") != "ok":
        raise RuntimeError(data)

    return data["solution"]["response"]


# Pagination
def get_page_url(page):
    if page == 1:
        return BASE_URL
    return f"{BASE_URL}?subcategory=PCI&only=3&order=pa&page={page}"


# Parsing
def parse_products(html):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    products = defaultdict(dict)


    for tag in soup.select("a.selectItem"):
        part = tag.get("data-noparte")
        if not part:
            continue

        p = products[part]

        for k, v in tag.attrs.items():
            if v and k not in p:
                p[k] = v
        p["manufacturer"] = p.get("data-marca")

        img = tag.select_one("picture source[type='image/webp']")
        if img and img.get("srcset"):
            p["image"] = img.get("srcset")

    # stock
    for tag in soup.select("a.add-to-cart-search-fast"):
        part = tag.get("data-noparte")
        if not part:
            continue

        products[part]["stock"] = tag.get("data-stock")
        products[part]["storelistingid"] = tag.get("data-upc")

    # shipping detection
    for block in soup.select("div.hoverable"):
        text = block.get_text(" ", strip=True)
        free_shipping = "Envío Gratis" in text

        link = block.select_one("a.selectItem[data-noparte]")
        if not link:
            continue

        part = link.get("data-noparte")
        if part in products:
            products[part]["shipping"] = 0 if free_shipping else None

    results = []

    for part, data in products.items():
        row = {
            "storelistingid": data.get("storelistingid"),
            "sku": part,
            "storeid": STORE_ID,
            "title": data.get("data-descripcion"),
            "manufacturer": data.get("data-marca"),
            "url": urljoin(JOIN_URL, data.get("href", "")),
            "availability": "InStock" if data.get("stock") else "OutOfStock",
            "price": data.get("data-price"),
            "currency": "MXN",
            "imageurl": urljoin(JOIN_URL, data.get("image")),
            "shippingprice": data.get("shipping"),
        }

        row["rawjson"] = row.copy()

        results.append(row)

    return results

# DB insert
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

# Main loop
def run():
    conn = psycopg.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )
    cursor = conn.cursor()

    session_id = "zegucom_session"
    fs_create_session(session_id)

    page = 1
    total = 0

    try:
        while True:
            url = get_page_url(page)
            print(f"[blue]Page {page}:[/blue] {url}")

            html = fs_get(url, session_id=session_id)

            if "No se encontraron productos" in html:
                break

            products = parse_products(html)

            if not products:
                break

            print(f"[cyan]Products found:[/cyan] {len(products)}")

            for p in products:
                try:
                    save_listing(cursor, conn, p)
                    total += 1
                    print(f"[green]Saved:[/green] {p['title']}")

                except Exception as e:
                    print(f"[red]DB error:[/red] {e}")
                    conn.rollback()

            page += 1
            time.sleep(1.2)

    finally:
        fs_destroy_session(session_id)
        cursor.close()
        conn.close()

    print(f"[green]Done. Total saved: {total}[/green]")


if __name__ == "__main__":
    run()