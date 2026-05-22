from playwright.sync_api import sync_playwright, Playwright
from rich import print
from dotenv import load_dotenv
import os
import psycopg
import json

load_dotenv()

#blocks loading images, videos and fonts, makes loading faster
def block_resources(route):
    if route.request.resource_type in ["image", "media", "font"]:
        route.abort()
    else:
        route.continue_()


def run(playwright: Playwright):
    conn = psycopg.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    cursor = conn.cursor()

    start_url = 'https://ddtech.mx/productos/componentes/tarjetas-de-video'
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    page.route("**/*", block_resources)
    page.goto(start_url)

    while True:
        for link in page.locator("h3.name a").all():
            url = link.get_attribute('href')

            if url is None:
                continue

            p = browser.new_page()
            p.route("**/*", block_resources)

            try:
                p.goto(url, timeout=15000)
            
                #scrape all the info from the site
                data = p.locator("#mp-data").text_content()
                json_data = json.loads(data)
                title = json_data["items"][0]["title"]
                product_id = json_data["items"][0]["id"]
                price = json_data["items"][0]["unit_price"]
                currency = json_data["items"][0]["currency_id"]
                stock = p.locator("div.stock-box span.value").text_content()
                img_url = p.locator("#owl-single-product a[data-lightbox]").first.get_attribute("href")
                ddtech_id = 1
                
                # insert into db
                cursor.execute(
                    """
                    INSERT INTO listing (
                        StoreListingId,
                        StoreId,
                        StoreTitle,
                        Link,
                        CreatedAt,
                        UpdatedAt,
                        LastseenAt,
                        CurrentPrice,
                        CurrentPriceUpdatedAt,
                        ImageUrl,
                        StockAmount,
                        RawJson,
                        Currency
                    )
                    VALUES (
                        %s, %s, %s, %s,
                        NOW(), NOW(), NOW(),
                        %s, NOW(),
                        %s, %s, %s, %s
                    )
                    ON CONFLICT (StoreId, StoreListingId) DO UPDATE SET
                        CurrentPrice = EXCLUDED.CurrentPrice,
                        LastseenAt = NOW(),
                        StockAmount = EXCLUDED.StockAmount;
                    """,
                    (
                        product_id,
                        ddtech_id,
                        title,
                        url,
                        price,
                        img_url,
                        stock,
                        json.dumps(json_data),
                        currency
                    )
                )
                conn.commit()
                print(f"[green]Saved:[/green] {title} (${price})")
                
            except Exception as e:
                print(f"[red]Failed on {url}: {e}[/red]")
                conn.rollback()
            finally:
                p.close()

        next_button = page.locator("a[rel='next']")
        if not next_button.is_visible():
            print("Reached last page")
            break

        next_button.click()
        page.wait_for_load_state("domcontentloaded")
    
    p.close()
    browser.close()
    cursor.close()


with sync_playwright() as playwright:
    run(playwright)
    