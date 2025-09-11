import asyncio
from playwright.async_api import async_playwright
import time
from .scrape_amazon import scrape_amazon
from .scrape_flipkart import scrape_flipkart
from .email_reports import send_report
# ===== CONFIG =====
PRODUCTS = [
    {
        "name": "iPhone 15 (Amazon)",
        "url": "https://www.amazon.in/Crucial-BX500-NAND-2-5-Inch-Internal/dp/B07YD579WM/ref=sr_1_2?crid=36RRRQVQ5MWEK&dib=eyJ2IjoiMSJ9.W25BKw_oWMGeCGKz3mxcSQVwVZJAGmRQUtDTdRyyzi-MKj3oLDT6TOvgqvaJF2Npd38XhNn63zUTazdFXlys1nB20Gr30AmjZsmTb2Kdu-R3SS0tN7ZAYPsOCCBy0gr8xtb07ogTWBXH-furqbPGP_9Q-ixdTaRq-QcFD5KC09pSP-KFcAd9trnbX8JN7oPaVfWa2mOwimLAdkHjfNoSXT4mnYAcwb12culiTj2YLHY.naEb4cdEBQMWdaH4ASxSciiBzDRcPC9Np0j2EO-ATj4&dib_tag=se&keywords=2.5%2Binch%2Bsata%2Bhdd&qid=1757223745&refinements=p_n_g-1004209391091%3A1464350031&rnid=1464345031&sprefix=2.5%2Bin%2Caps%2C251&sr=8-2&th=1",
        "threshold": 70
    },
    {
        "name": "Laptop (Flipkart)",
        "url": "https://www.flipkart.com/d-link-dir-615-wireless-router-2-4-ghz-300-mbps-wifi-speed-single-band-external-antenna-ethernet-cable-broadband/p/itme3xwg9x9jgsyh?pid=RTRE3XW76EHCJUGH&lid=LSTRTRE3XW76EHCJUGHN7FTWG&marketplace=FLIPKART&store=6bo%2F70k%2F2a2&spotlightTagId=default_BestsellerId_6bo%2F70k%2F2a2&srno=b_1_3&otracker=hp_rich_navigation_4_1.navigationCard.RICH_NAVIGATION_Electronics~Laptop%2BAccessories~Router_W2AXELWSLQML&otracker1=hp_rich_navigation_PINNED_neo%2Fmerchandising_NA_NAV_EXPANDABLE_navigationCard_cc_4_L2_view-all&fm=organic&iid=bddc70e1-34f0-4167-8c5a-f09fd3bb8505.RTRE3XW76EHCJUGH.SEARCH&ppt=browse&ppn=browse&ssid=7nblxb76e80000001757572172080",
        "threshold": 500000
    }
]

CHECK_INTERVAL = 60 * 60  # check every 1 hour

# ===== EMAIL CONFIG =====
SENDER_EMAIL = "youremail@gmail.com"
SENDER_PASSWORD = "your-app-password"   # Use App Password for Gmail
RECEIVER_EMAIL = "targetemail@gmail.com"


async def scrape_product(page, product):
    """Scrape price info for Amazon or Flipkart product."""
    url = product["url"]

    current_price, original_price, discount = 10e9, 10e9, 0.0

    if "amazon" in url:
        amazon_scraped_prices = await scrape_amazon(url, page)
        if amazon_scraped_prices is None:
            return None
        current_price, original_price = amazon_scraped_prices

    elif "flipkart" in url:
        flipkart_scraped_prices = await scrape_flipkart(url, page)
        print(f"{flipkart_scraped_prices=}")
        if flipkart_scraped_prices is None:
            return None
        current_price, original_price = flipkart_scraped_prices


    discount = round(((original_price - current_price) / original_price) * 100, 2) if original_price > current_price else 0

    return {
        "name": product["name"],
        "url": url,
        "current_price": current_price,
        "original_price": original_price,
        "discount": discount,
        "threshold": product["threshold"],
        "status": "✅ Below Threshold" if current_price <= product["threshold"] else "❌ Above Threshold"
    }


async def track_prices():
    """Launch Playwright and track all products."""
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False
            #                               ,proxy={
            #     "server": "socks5://127.0.0.1:9050"
            # }
            )
        context = await browser.new_context(user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ))
        page = await context.new_page()

        for product in PRODUCTS:
            info = await scrape_product(page, product)
            if info:
                results.append(info)
            else:
                print(f"❌ Failed to fetch price for {product['name']}")

        await browser.close()

    if results:
        # print(results)
        send_report(results)



async def main():
    await track_prices()

if __name__ == "__main__":
    asyncio.run(track_prices())
    # while True:
    #     time.sleep(CHECK_INTERVAL)
