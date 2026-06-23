from rich import print
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import psycopg
import requests
import json
import re
import os
import time

load_dotenv()

FLARESOLVERR_URL = "http://localhost:8191/v1"
BASE_URL = "https://intercompras.com/c/tarjetas-video-graficas-gpu-839?page={page}"
STORE_ID = 7


def fs_create_session(session_id="intercompras_session"):
    r = requests.post(FLARESOLVERR_URL, json={"cmd": "sessions.create", "session": session_id}, timeout=60)
    r.raise_for_status()
    return r.json()


def fs_destroy_session(session_id="intercompras_session"):
    try:
        requests.post(FLARESOLVERR_URL, json={"cmd": "sessions.destroy", "session": session_id}, timeout=30)
    except Exception:
        pass


def fs_get(url, session_id="intercompras_session"):
    payload = {"cmd": "request.get", "url": url, "session": session_id, "maxTimeout": 60000}
    r = requests.post(FLARESOLVERR_URL, json=payload, timeout=70)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "ok":
        raise RuntimeError(f"FlareSolverr error: {data.get('message')}")
    return data["solution"]["response"]


def get_spec(card, label):
    for div in card.select("div.divProductListFeature"):
        strong = div.find("strong")
        if strong and label.lower() in strong.get_text().lower():
            # get the text after the strong tag
            text = div.get_text(strip=True)
            label_text = strong.get_text(strip=True)
            return text[len(label_text):].strip()
    return None


def extract_listings(html):
    soup = BeautifulSoup(html, "html.parser")

    # Check for no products page
    if soup.find("div", class_="lh150tac"):
        return None  # signals end of pagination

    cards = soup.select("div.divContentProductInfo")
    listings = []

    for card in cards:
        try:
            # Title and link
            title_el = card.select_one("a.spanProductListInfoTitle")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            link = title_el.get("href", "")
            if link and not link.startswith("http"):
                link = "https://intercompras.com" + link

            # Product ID from link (last segment)
            id_match = re.search(r'-(\d+)$', link)
            storelistingid = id_match.group(1) if id_match else None
            if not storelistingid:
                continue

            # SKU/Model
            model_div = card.select_one("div.divProductListFeature.model")
            sku = None
            if model_div:
                text = model_div.get_text(strip=True)
                sku = text.replace("Modelo:", "").strip()

            # Structured specs
            gpumodel = get_spec(card, "Procesador gráfico")
            memorytype = get_spec(card, "Tipo de memoria de adaptador gráfico")
            vramgb_raw = get_spec(card, "Gráficos discretos memoria del adaptado")
            buswidth_raw = get_spec(card, "Ancho de datos")
            interfaceversion_raw = get_spec(card, "Tipo de interfaz")

            vramgb = int(re.search(r'\d+', vramgb_raw).group()) if vramgb_raw and re.search(r'\d+', vramgb_raw) else None
            buswidth = int(re.search(r'\d+', buswidth_raw).group()) if buswidth_raw and re.search(r'\d+', buswidth_raw) else None
            if interfaceversion_raw:
                interfaceversion = re.sub(r'PCI[\s-]?Express\s*', '', interfaceversion_raw, flags=re.IGNORECASE).strip()
                interfaceversion = re.sub(r'^x\d+\s*', '', interfaceversion).strip()
            else:
                interfaceversion = None

            # Price
            price_el = card.select_one("div.divProductListPrice")
            price = None
            if price_el:
                price_text = price_el.get_text(strip=True).replace("$", "").replace(",", "").strip()
                try:
                    price = float(price_text)
                except ValueError:
                    pass

            # Shipping price
            shipping_el = card.select_one("div.divProductListShipping span")
            shippingprice = None
            if shipping_el:
                shipping_text = shipping_el.get_text(strip=True)
                if "gratis" in shipping_text.lower():
                    shippingprice = 0
                else:
                    shipping_match = re.search(r'[\d,]+\.?\d*', shipping_text.replace(",", ""))
                    if shipping_match:
                        shippingprice = float(shipping_match.group())

            # Stock
            stock_el = card.select_one("span.available")
            stock = int(stock_el.get_text(strip=True)) if stock_el else None
            availability = "InStock" if stock and stock > 0 else "OutOfStock"

            # Image
            img_el = card.select_one("div.divProductListInfoImage img:not(.pl-brand img)")
            # get the product image, not the brand logo
            imgs = card.select("div.divProductListInfoImage img")
            imageurl = None
            for img in imgs:
                src = img.get("src", "")
                if "logofabricante" not in src:
                    imageurl = src
                    break

            listings.append({
                "storelistingid": storelistingid,
                "title": title,
                "link": link,
                "sku": sku,
                "gpumodel": gpumodel,
                "memorytype": memorytype.upper() if memorytype else None,
                "vramgb": vramgb,
                "buswidth": buswidth,
                "interfaceversion": interfaceversion,
                "price": price,
                "shippingprice": shippingprice,
                "stock": stock,
                "availability": availability,
                "imageurl": imageurl,
            })

        except Exception as e:
            print(f"[red]Failed to parse card:[/red] {e}")
            continue

    return listings


def save_listing(cursor, conn, listing):
    cursor.execute("""
        INSERT INTO listing (
            StoreListingId, StoreId, StoreTitle, Link,
            AvailabilityStatus, CreatedAt, UpdatedAt, LastSeenAt,
            CurrentPrice, CurrentPriceUpdatedAt, ImageUrl,
            RawJson, Currency, ShippingPrice, StockAmount
        )
        VALUES (
            %s, %s, %s, %s,
            %s, NOW(), NOW(), NOW(),
            %s, NOW(), %s,
            %s, 'MXN', %s, %s
        )
        ON CONFLICT (StoreId, StoreListingId)
        DO UPDATE SET
            CurrentPrice = EXCLUDED.CurrentPrice,
            AvailabilityStatus = EXCLUDED.AvailabilityStatus,
            LastSeenAt = NOW(),
            UpdatedAt = NOW(),
            ImageUrl = EXCLUDED.ImageUrl,
            ShippingPrice = EXCLUDED.ShippingPrice,
            StockAmount = EXCLUDED.StockAmount,
            RawJson = EXCLUDED.RawJson
        RETURNING listingid, currentprice, shippingprice, currency;
    """, (
        listing["storelistingid"],
        STORE_ID,
        listing["title"],
        listing["link"],
        listing["availability"],
        listing["price"],
        listing["imageurl"],
        psycopg.types.json.Json(listing),
        listing["shippingprice"],
        listing["stock"],
    ))

    listingid, currentprice, shippingprice, currency = cursor.fetchone()

    cursor.execute("""
        INSERT INTO pricesnapshot (listingid, currency, price, capturedat, shippingprice)
        VALUES (%s, %s, %s, NOW(), %s)
    """, (listingid, currency, currentprice, shippingprice))

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

    session_id = "intercompras_session"
    fs_create_session(session_id)
    total_saved = 0

    try:
        for page in range(1, 11):
            url = BASE_URL.format(page=page)
            print(f"[blue]Fetching page {page}:[/blue] {url}")

            try:
                html = fs_get(url, session_id)
            except Exception as e:
                print(f"[red]FlareSolverr failed on page {page}:[/red] {e}")
                break

            listings = extract_listings(html)

            if listings is None:
                print(f"[cyan]No products on page {page}, stopping.[/cyan]")
                break

            if not listings:
                print(f"[yellow]No cards parsed on page {page}, stopping.[/yellow]")
                break

            print(f"[cyan]Found {len(listings)} listings on page {page}[/cyan]")

            for listing in listings:
                try:
                    save_listing(cursor, conn, listing)
                    total_saved += 1
                    print(f"[green]Saved:[/green] {listing['title']} | ${listing['price']}")
                except Exception as e:
                    conn.rollback()
                    print(f"[red]Failed to save:[/red] {listing['title']}\n{e}")

            time.sleep(2)

    finally:
        fs_destroy_session(session_id)
        cursor.close()
        conn.close()

    print(f"[green]Finished. Total saved: {total_saved}[/green]")


if __name__ == "__main__":
    run()