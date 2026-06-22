from camoufox.sync_api import Camoufox
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from rich import print
import psycopg
import os
import re
import time

load_dotenv()

BASE_URL = "https://listado.mercadolibre.com.mx/computacion/componentes-pc/tarjetas/tarjetas-video/nuevo/_Tienda_all_MEMORY*SIZE_6-*_NoIndex_True"
STORE_ID = 5  # Mercado Libre
RESULTS_PER_PAGE = 48


def extract_listings(html):
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("li.ui-search-layout__item")
    listings = []

    for card in cards:
        try:
            title_el = card.select_one("h3.poly-component__title-wrapper a.poly-component__title")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            link = title_el["href"]

            # Extract product id (p/MLM12345678) and item id (wid=MLM...)
            product_id_match = re.search(r'/p/(MLM\d+)', link)
            item_id_match = re.search(r'wid=(MLM\d+)', link)
            product_id = product_id_match.group(1) if product_id_match else None
            item_id = item_id_match.group(1) if item_id_match else None

            storelistingid = product_id or item_id
            if not storelistingid:
                continue

            seller_el = card.select_one("span.poly-component__seller")
            seller = seller_el.get_text(strip=True) if seller_el else None

            price_current_el = card.select_one("div.poly-price__current .andes-money-amount__fraction")
            price_current = price_current_el.get_text(strip=True) if price_current_el else None
            price_current = int(price_current.replace(",", "")) if price_current else None

            price_original_el = card.select_one("s.andes-money-amount--previous .andes-money-amount__fraction")
            price_original = price_original_el.get_text(strip=True) if price_original_el else None
            price_original = int(price_original.replace(",", "")) if price_original else None

            image_el = card.select_one("img.poly-component__picture")
            image = image_el.get("src") if image_el else None

            # Shipping
            shipping_el = card.select_one("div.poly-shipping-v2__item")
            shipping_text = shipping_el.get_text(strip=True) if shipping_el else None
            free_shipping = bool(shipping_text and "gratis" in shipping_text.lower())
            shippingprice = 0 if free_shipping else None

            listings.append({
                "storelistingid": storelistingid,
                "title": title,
                "link": link.split("#")[0],
                "seller": seller,
                "price_current": price_current,
                "price_original": price_original,
                "imageurl": image,
                "shippingprice": shippingprice,
            })

        except Exception as e:
            print(f"[red]Failed to parse card:[/red] {e}")
            continue

    return listings


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
            'InStock', NOW(), NOW(), NOW(),
            %s, NOW(), %s,
            %s, 'MXN', %s
        )
        ON CONFLICT (StoreId, StoreListingId)
        DO UPDATE SET
            CurrentPrice = EXCLUDED.CurrentPrice,
            LastSeenAt = NOW(),
            RawJson = EXCLUDED.RawJson,
            UpdatedAt = NOW(),
            ImageUrl = EXCLUDED.ImageUrl,
            ShippingPrice = EXCLUDED.ShippingPrice
        RETURNING listingid, currentprice, shippingprice, currency;
        """,
        (
            listing["storelistingid"],
            STORE_ID,
            listing["title"],
            listing["link"],
            listing["price_current"],
            listing["imageurl"],
            psycopg.types.json.Json(listing),
            listing["shippingprice"],
        )
    )
    
    listingid, currentprice, shippingprice, currency = cursor.fetchone()

    cursor.execute(
        """
        INSERT INTO pricesnapshot (listingid, currency, price, capturedat, shippingprice)
        VALUES (%s, %s, %s, NOW(), %s);
        """,
        (listingid, currency, currentprice, shippingprice)
    )
    conn.commit()


def run():
    conn = psycopg.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
    )
    cursor = conn.cursor()

    total_saved = 0
    offset = 0

    with Camoufox(headless=False) as browser:
        page = browser.new_page()

        while True:
            if offset == 0:
                url = BASE_URL
            else:
                url = BASE_URL.replace("_NoIndex_True", f"_Desde_{offset + 1}_NoIndex_True")

            print(f"[blue]Fetching:[/blue] {url}")
            page.goto(url)
            page.wait_for_timeout(5000)

            html = page.content()
            listings = extract_listings(html)

            if not listings:
                print("[cyan]No more listings found, stopping.[/cyan]")
                break

            print(f"[cyan]Found {len(listings)} listings on this page[/cyan]")

            for listing in listings:
                try:
                    save_listing(cursor, conn, listing)
                    total_saved += 1
                    print(f"[green]Saved:[/green] {listing['title']} | ${listing['price_current']}")
                except Exception as e:
                    conn.rollback()
                    print(f"[red]Failed to save:[/red] {listing['title']}\n{e}")

            offset += RESULTS_PER_PAGE
            time.sleep(3)

        page.close()

    cursor.close()
    conn.close()
    print(f"[green]Finished. Total listings saved: {total_saved}[/green]")


if __name__ == "__main__":
    run()