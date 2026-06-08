import requests
import json
import psycopg
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from urllib.parse import urljoin

load_dotenv()

FLARESOLVERR_URL = "http://localhost:8191/v1"
SESSION_ID = "ddtech_session"
BASE_URL = "https://ddtech.mx"

#skip bundles that are listed under the GPU category
SKIP_KEYWORDS = ["bundle", "combo", "fuente", "tarjeta madre", "kit"]

def is_bundle(title):
    title_lower = title.lower()
    return any(kw in title_lower for kw in SKIP_KEYWORDS)

def create_session():
    requests.post(FLARESOLVERR_URL, json={
        "cmd": "sessions.create",
        "session": SESSION_ID
    })

def destroy_session():
    requests.post(FLARESOLVERR_URL, json={
        "cmd": "sessions.destroy",
        "session": SESSION_ID
    })

def fs_get(url):
    resp = requests.post(FLARESOLVERR_URL, json={
        "cmd": "request.get",
        "url": url,
        "session": SESSION_ID,
        "maxTimeout": 60000
    })
    return resp.json()["solution"]["response"]

def parse_price(price_str):
    if not price_str:
        return None
    return float(price_str.strip().replace("$", "").replace(",", ""))

def run():
    conn = psycopg.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    cursor = conn.cursor()
    create_session()

    try:
        page_url = f"{BASE_URL}/productos/componentes/tarjetas-de-video"

        while True:
            print(f"Scraping: {page_url}")
            html = fs_get(page_url)
            soup = BeautifulSoup(html, "html.parser")

            for product_div in soup.select("div.product"):
                try:
                    title_el = product_div.select_one("h3.name a")
                    if not title_el:
                        continue

                    title = title_el.text.strip()
                    url = title_el.get("href")

                    if is_bundle(title):
                        print(f"Skipping bundle: {title}")
                        continue

                    price_el = product_div.select_one("span.price")
                    price = parse_price(price_el.text) if price_el else None

                    product_id_el = product_div.select_one("a.add-cart[data-product-id]")
                    if product_id_el:
                        product_id = product_id_el.get("data-product-id")
                    else:
                        # fallback: extract id from the product URL
                        import re
                        match = re.search(r'\?id=(\d+)', url) if url else None
                        product_id = match.group(1) if match else None

                    img_el = product_div.select_one(".product-image .image img")
                    # img may be lazy loaded via data-echo
                    img_url = img_el.get("src") or img_el.get("data-echo") if img_el else None
                    if img_url and "blank.gif" in img_url:
                        img_url = img_el.get("data-echo")

                    stock_el = product_div.select_one("span.label.with-stock")
                    availability = "InStock" if stock_el else "OutOfStock"

                    if not product_id:
                        print(f"Skipping (no product_id): {title}")
                        continue

                    cursor.execute("""
                        INSERT INTO listing (
                            StoreListingId, StoreId, StoreTitle, Link,
                            CreatedAt, UpdatedAt, LastseenAt,
                            CurrentPrice, CurrentPriceUpdatedAt,
                            ImageUrl, AvailabilityStatus, RawJson, Currency
                        )
                        VALUES (%s, %s, %s, %s, NOW(), NOW(), NOW(), %s, NOW(), %s, %s, %s, %s)
                        ON CONFLICT (StoreId, StoreListingId) DO UPDATE SET
                            CurrentPrice = EXCLUDED.CurrentPrice,
                            LastseenAt = NOW(),
                            AvailabilityStatus = EXCLUDED.AvailabilityStatus;
                    """, (product_id, 1, title, url, price, img_url, availability, json.dumps({}), "MXN"))
                    conn.commit()
                    print(f"Saved: {title} (${price})")

                except Exception as e:
                    print(f"Failed on product: {e}")
                    conn.rollback()

            next_link = soup.select_one("a[rel='next']")
            if not next_link or next_link.get("href") == "javascript:return false;":
                print("Reached last page")
                break
            page_url = next_link.get("href")

    finally:
        destroy_session()
        cursor.close()
        conn.close()

run()