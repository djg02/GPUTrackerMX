from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import urllib.parse
import re
from dotenv import load_dotenv
import psycopg
import os

load_dotenv()


URL = "https://www.amazon.com.mx/s?i=electronics&rh=n%3A12005806011%2Cp_36%3A330000-%2Cp_n_condition-type%3A21214164011%2Cp_n_g-1003124131111%3A23720434011%2Cp_n_g-101013604837111%3A213277243011%257C82315745011%257C82315751011%2Cp_n_availability%3A9841525011&dc&qid=1787447431&rnid=9841523011&ref=sr_nr_p_n_availability_2&ds=v1%3A4sWRKZuJLlrjr4ls3jZfasY67LR5Hk7zDiokvBU42FU"

BASE_URL = "https://www.amazon.com.mx"

conn = psycopg.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", 5432)),
)
cursor = conn.cursor()

def _parse_price(raw):
    if not raw:
        return None

    cleaned = (
        raw
        .replace("$", "")
        .replace(",", "")
        .strip()
    )

    try:
        return int(round(float(cleaned)))
    except ValueError:
        return None

sponsored_count = 0

def extract_listings(html):
    global sponsored_count

    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div[data-component-type='s-search-result']")

    listings = []

    for card in cards:
        try:
            card_text = card.get_text(" ", strip=True).lower()
            if "patrocinado" in card_text:
                sponsored_count += 1
                continue

            asin = card.get("data-asin")
            if not asin:
                continue

            title_el = card.select_one("div[data-cy='title-recipe'] h2 span")
            if not title_el:
                continue
            title = title_el.get_text(" ", strip=True)

            link_el = card.select_one("div[data-cy='title-recipe'] a")
            if not link_el:
                continue
            href = link_el.get("href")
            if not href:
                continue
            link = urllib.parse.urljoin("https://www.amazon.com.mx", href).split("?")[0]

            # Delivery block / OOS signal
            delivery_block = card.select_one("div[data-cy='delivery-recipe']")
            delivery_text = delivery_block.get_text(" ", strip=True).lower() if delivery_block else ""
            is_oos = "no disponible por el momento" in delivery_text
            shippingprice = 0 if "gratis" in delivery_text else None

            # CurrentPrice (with fallback to secondary/marketplace offer)
            price_block = card.select_one("div[data-cy='price-recipe']")
            price_current = None
            price_original = None

            if price_block:
                current_el = price_block.select_one(
                    "span.a-price:not(.a-text-price) span.a-offscreen"
                )
                if current_el:
                    price_current = _parse_price(current_el.get_text(strip=True))

                original_el = price_block.select_one(
                    "span.a-price.a-text-price[data-a-strike='true'] span.a-offscreen"
                )
                if original_el:
                    price_original = _parse_price(original_el.get_text(strip=True))

            if price_current is None and not is_oos:
                secondary_block = card.select_one("div[data-cy='secondary-offer-recipe']")
                if secondary_block:
                    secondary_price_el = secondary_block.select_one("span.a-color-base")
                    if secondary_price_el:
                        price_current = _parse_price(secondary_price_el.get_text(strip=True))

            if price_current is None and not is_oos:
                # No price anywhere and no explicit OOS marker -- ambiguous, skip
                continue

            # ImageUrl
            image_el = card.select_one("img.s-image")
            image = None
            if image_el:
                image = image_el.get("src") or image_el.get("data-src")

            availability = "OutOfStock" if is_oos else "InStock"

            listing = {
                "storelistingid": asin,
                "title": title,
                "link": link,
                "availability": availability,
                "price_current": price_current,
                "price_original": price_original,
                "imageurl": image,
                "shippingprice": shippingprice,
            }

            listings.append(listing)

        except Exception as e:
            print(f"[red]Failed to parse Amazon card:[/red] {e}")
            continue

    return listings

def get_total_pages(html):
    soup = BeautifulSoup(html, "html.parser")

    page_numbers = []
    for span in soup.select("span.s-pagination-item"):
        if "s-pagination-ellipsis" in span.get("class", []):
            continue
        text = span.get_text(strip=True)
        if text.isdigit():
            page_numbers.append(int(text))

    return max(page_numbers) if page_numbers else 1


def set_page(url, page_number):
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    qs["page"] = [str(page_number)]
    # drop session-bound params
    qs.pop("xpid", None)
    qs.pop("qid", None)
    qs.pop("ref", None)
    new_qs = urllib.parse.urlencode(qs, doseq=True, safe="|,:")
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_qs}"

STORE_ID = 8  # Amazon MX

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
            %s, 'MXN', %s
        )
        ON CONFLICT (StoreId, StoreListingId)
        DO UPDATE SET
            CurrentPrice = COALESCE(EXCLUDED.CurrentPrice, listing.CurrentPrice),
            AvailabilityStatus = EXCLUDED.AvailabilityStatus,
            LastSeenAt = NOW(),
            RawJson = EXCLUDED.RawJson,
            UpdatedAt = NOW(),
            ImageUrl = EXCLUDED.ImageUrl,
            ShippingPrice = COALESCE(EXCLUDED.ShippingPrice, listing.ShippingPrice)
        RETURNING listingid, currentprice, shippingprice, currency;
        """,
        (
            listing["storelistingid"],
            STORE_ID,
            listing["title"],
            listing["link"],
            listing["availability"],
            listing["price_current"],
            listing["imageurl"],
            psycopg.types.json.Json(listing),
            listing["shippingprice"],
        )
    )

    listingid, currentprice, shippingprice, currency = cursor.fetchone()

    if listing["price_current"] is not None and listing["availability"] == "InStock":
        cursor.execute(
            """
            INSERT INTO pricesnapshot (listingid, currency, price, capturedat, shippingprice)
            VALUES (%s, %s, %s, NOW(), %s);
            """,
            (listingid, currency, currentprice, shippingprice)
        )

    conn.commit()

total_saved = 0

with sync_playwright() as p:

    context = p.firefox.launch_persistent_context(
        "scrapers/Amazon/amazon-profile",
        headless=True,
        locale="es-MX",
    )

    page = (
        context.pages[0]
        if context.pages
        else context.new_page()
    )

    url = URL
    page_number = 1

    response = page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)
    html = page.content()

    total_pages = get_total_pages(html)
    print(f"Total pages detected: {total_pages}")

    while page_number <= total_pages:
        if page_number > 1:
            url = set_page(URL, page_number)
            print()
            print("=" * 80)
            print(f"Opening Amazon page {page_number}...")
            print(url)
            response = page.goto(url, wait_until="domcontentloaded", timeout=60000)
            print("Status:", response.status if response else None)
            page.wait_for_timeout(5000)
            html = page.content()

        listings = extract_listings(html)
        print()
        print(f"Found {len(listings)} listings")
        print("=" * 80)

        for listing in listings:
            try:
                save_listing(cursor, conn, listing)
                total_saved += 1
                print(f"Saved: {listing['title']} | ${listing['price_current']}")
            except Exception as e:
                conn.rollback()
                print(f"Failed to save: {listing['title']}\n{e}")

        page_number += 1
        page.wait_for_timeout(3000)

    print()
    print(f"Finished. Pages scraped: {page_number - 1}")
    cursor.close()
    conn.close()
    print(f"\nFinished. Total listings saved: {total_saved}")
    print(f"\nTotal listings skipped: {sponsored_count}")

    context.close()