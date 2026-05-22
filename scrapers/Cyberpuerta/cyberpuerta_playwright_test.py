from playwright.sync_api import sync_playwright, Playwright
from rich import print
from dotenv import load_dotenv
from urllib.parse import urljoin
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


    start_url = 'https://www.cyberpuerta.mx/Computo-Hardware/Componentes/Tarjetas-de-Video/'
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    page.route("**/*", block_resources)
    page.goto(start_url)

    while True:
        stable_rounds = 0
        previous_count = 0
        while stable_rounds < 5:
            page.mouse.wheel(0, 1000)
            page.wait_for_timeout(500)

            current_count = page.locator(
                "a.cp-product-info-dne--catalog-card"
            ).count()
            if current_count == previous_count:
                stable_rounds += 1
            else:
                stable_rounds = 0

            previous_count = current_count

        links = page.locator("a.cp-product-info-dne--catalog-card")
        print(f"Final count: {links.count()}")
        for link in links.all():
            base = "https://www.cyberpuerta.mx"
            url = link.get_attribute("href")
            url = urljoin(base, url)
             
            if url is None:
                continue

            p = browser.new_page()
            p.route("**/*", block_resources)

            try:
                p.goto(url, timeout=15000)
                print(f"[green]Saved:[/green] {url}")
                
            except Exception as e:
                print(f"[red]Failed on {url}: {e}[/red]")
                
            finally:
                p.close()

        next_button = page.locator("button[data-testid='next-page-paginator']")
        if next_button.is_disabled():
            print("Reached last page")
            break
        next_button.click()
        page.wait_for_timeout(2000)
    
with sync_playwright() as playwright:
    run(playwright)