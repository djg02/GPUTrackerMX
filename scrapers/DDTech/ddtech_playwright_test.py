from playwright.sync_api import sync_playwright, Playwright
from rich import print
import json

def run (playwright: Playwright):
    start_url = 'https://ddtech.mx/productos/componentes/tarjetas-de-video'
    chrome = playwright.chromium
    browser = chrome.launch(headless=False)
    page = browser.new_page()

    #blocks loading images, videos and fonts, makes loading faster
    page.route("**/*",lambda route: route.abort()
    if route.request.resource_type in ["image", "media", "font"]
    else route.continue_())

    page.goto(start_url)

    while True:
        for link in page.locator("h3.name a").all():
            p = browser.new_page()
            p.route("**/*",lambda route: route.abort()
            if route.request.resource_type in ["image", "media", "font"]
            else route.continue_())
            url = link.get_attribute('href')

            if url is not None:
                p.goto(url)
            else:
                p.close()

            data = p.locator("#mp-data").text_content()
            json_data = json.loads(data)
            print(json_data["items"][0]["title"])
            print(json_data["items"][0]["id"])
            print(json_data["items"][0]["unit_price"])
            print(json_data["items"][0]["currency_id"])
            stock = p.locator("div.stock-box span.value").text_content()
            img_url = p.locator("#owl-single-product a[data-lightbox]").first.get_attribute("href")
            print(stock)
            print(url)
            print(img_url)
            p.close()
        next_button = page.locator("a[rel='next']")
        if not next_button.is_visible():
            print("Reached last page")
            break

        next_button.click()
        page.wait_for_load_state("networkidle")


with sync_playwright() as playwright:
    run(playwright)