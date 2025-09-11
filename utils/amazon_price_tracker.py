# price_tracker_playwright_flipkart.py
import asyncio
from playwright.async_api import async_playwright
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
import os

# ===== CONFIG =====
PRODUCTS = [
    # {
    #     "name": "D-Link DIR-615 (Amazon test)",
    #     "url": "https://www.amazon.in/Crucial-BX500-NAND-2-5-Inch-Internal/dp/B07YD579WM/ref=sr_1_2?crid=36RRRQVQ5MWEK&dib=eyJ2IjoiMSJ9.W25BKw_oWMGeCGKz3mxcSQVwVZJAGmRQUtDTdRyyzi-MKj3oLDT6TOvgqvaJF2Npd38XhNn63zUTazdFXlys1nB20Gr30AmjZsmTb2Kdu-R3SS0tN7ZAYPsOCCBy0gr8xtb07ogTWBXH-furqbPGP_9Q-ixdTaRq-QcFD5KC09pSP-KFcAd9trnbX8JN7oPaVfWa2mOwimLAdkHjfNoSXT4mnYAcwb12culiTj2YLHY.naEb4cdEBQMWdaH4ASxSciiBzDRcPC9Np0j2EO-ATj4&dib_tag=se&keywords=2.5%2Binch%2Bsata%2Bhdd&qid=1757223745&refinements=p_n_g-1004209391091%3A1464350031&rnid=1464345031&sprefix=2.5%2Bin%2Caps%2C251&sr=8-2&th=1",
    #     "threshold": 1500
    # },
    {
        "name": "D-Link DIR-615 (Flipkart test)",
        "url": "https://www.flipkart.com/d-link-dir-615-wireless-router-2-4-ghz-300-mbps-wifi-speed-single-band-external-antenna-ethernet-cable-broadband/p/itme3xwg9x9jgsyh?pid=RTRE3XW76EHCJUGH&lid=LSTRTRE3XW76EHCJUGHN7FTWG&marketplace=FLIPKART&store=6bo%2F70k%2F2a2&spotlightTagId=default_BestsellerId_6bo%2F70k%2F2a2&srno=b_1_3&otracker=hp_rich_navigation_4_1.navigationCard.RICH_NAVIGATION_Electronics~Laptop%2BAccessories~Router_W2AXELWSLQML&otracker1=hp_rich_navigation_PINNED_neo%2Fmerchandising_NA_NAV_EXPANDABLE_navigationCard_cc_4_L2_view-all&fm=organic&iid=bddc70e1-34f0-4167-8c5a-f09fd3bb8505.RTRE3XW76EHCJUGH.SEARCH&ppt=browse&ppn=browse&ssid=7nblxb76e80000001757572172080",
        "threshold": 1500
    },
]

CHECK_INTERVAL = 60 * 60  # seconds

# ===== EMAIL CONFIG (fill these) =====
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "youremail@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "your-app-password")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "targetemail@gmail.com")

DEBUG = True  # set to False to silence debug output


# ---------- Flipkart scraper (robust) ----------
import statistics

async def scrape_flipkart(page, product):
    url = product["url"]
    await page.goto(url, wait_until="networkidle")

    elements = page.locator("xpath=//*[contains(text(),'₹')]")
    count = await elements.count()

    prices = []
    for i in range(count):
        text = (await elements.nth(i).inner_text()).strip()
        if not text:
            continue

        # Skip unwanted text
        lowered = text.lower()
        if any(skip in lowered for skip in [
            "month", "emi", "delivery", "fee", "off", "save", 
            "protect", "promise", "cashback", "card", "upto", "quarter"
        ]):
            continue
        if text.startswith("+") or "up to" in lowered:
            continue

        import re
        match = re.search(r"₹\s?([\d,]+(?:\.\d{1,2})?)", text)
        if match:
            price = float(match.group(1).replace(",", ""))
            prices.append((price, text))

    if not prices:
        print(f"Flipkart: No price found for {product['name']}")
        return None

    values = [p for p, _ in prices]

    import collections

    # Outlier filtering: remove prices far below median
    median_val = statistics.median(values)
    cutoff = 0.7 * median_val
    filtered = [(p, t) for p, t in prices if p >= cutoff]

    if not filtered:
        filtered = prices  # fallback

    values_only = [p for p, _ in filtered]

    # Pick the most frequent price as current (mode)
    counter = collections.Counter(values_only)
    current_price = counter.most_common(1)[0][0]

    # Original = max price > current
    larger_prices = [p for p in values_only if p > current_price]
    original_price = max(larger_prices) if larger_prices else current_price


    discount = round(((original_price - current_price) / original_price) * 100, 2) if original_price > current_price else 0.0

    if DEBUG:
        print(f"\nDEBUG - {product['name']}")
        print("All captured prices:", prices)
        print("Filtered prices:", filtered)
        print("Median value:", median_val)
        print("Current price:", current_price, "| Original price:", original_price)

    return {
        "name": product["name"],
        "url": url,
        "current_price": current_price,
        "original_price": original_price,
        "discount": discount,
        "threshold": product["threshold"],
        "status": "✅ Below Threshold" if current_price <= product["threshold"] else "❌ Above Threshold"
    }



# ---------- minimal Amazon scraper (safe fallback) ----------
async def scrape_amazon(page, product):
    url = product["url"]
    await page.goto(url, wait_until="networkidle")

    # Try JSON-LD or common selectors
    try:
        res = await page.evaluate(r"""
        () => {
          function parsePrice(text){
            if(!text) return null;
            const m = text.match(/₹\s?([\d,]+)/);
            if(!m) return null;
            return parseFloat(m[1].replace(/,/g,''));
          }
          // JSON-LD
          const ld = Array.from(document.querySelectorAll('script[type="application/ld+json"]')).map(s=>s.textContent).filter(Boolean);
          for(const t of ld){
            try {
              const j = JSON.parse(t);
              const found = [];
              (function walk(o){ if(!o||typeof o!=='object') return; if('price' in o) found.push(parseFloat(String(o.price))); for(const k in o) walk(o[k]); })(j);
              if(found.length) return {current: found[0], original: null};
            }catch(e){}
          }
          // selectors
          const selCandidates = [
            '#priceblock_dealprice', '#priceblock_ourprice', 'span.a-price > span.a-offscreen',
            'span.a-price-whole'
          ];
          for(const s of selCandidates){
            const el = document.querySelector(s);
            if(el){
              const p = parsePrice(el.innerText || el.textContent || el.value);
              if(p) return {current:p, original:null};
            }
          }
          // fallback to visible large ₹ elements
          const els = Array.from(document.querySelectorAll('body *')).filter(e=> (e.innerText||'').includes('₹') && e.offsetParent !== null);
          els.sort((a,b)=> (parseFloat(window.getComputedStyle(b).fontSize||0) - parseFloat(window.getComputedStyle(a).fontSize||0)));
          for(const e of els){
            const p = parsePrice(e.innerText);
            if(p) return {current:p, original:null};
          }
          return null;
        }
        """)
    except Exception as e:
        if DEBUG:
            print("Amazon evaluate error:", e)
        res = None

    if not res:
        if DEBUG:
            print("Amazon: failed to find price")
        return None

    current_price = res.get("current")
    original_price = res.get("original") or current_price
    discount = round(((original_price - current_price) / original_price) * 100, 2) if original_price > current_price else 0.0

    return {
        "name": product["name"],
        "url": url,
        "current_price": float(current_price),
        "original_price": float(original_price),
        "discount": discount,
        "threshold": product["threshold"],
        "status": "✅ Below Threshold" if float(current_price) <= product["threshold"] else "❌ Above Threshold"
    }

# ---------- orchestrator and email ----------
async def track_once():
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36")
        )
        page = await context.new_page()

        for product in PRODUCTS:
            url = product["url"]
            if "flipkart" in url:
                info = await scrape_flipkart(page, product)
            elif "amazon" in url:
                info = await scrape_amazon(page, product)
            else:
                info = None

            if info:
                results.append(info)
            else:
                print(f"Failed to fetch price for {product['name']}")

        await browser.close()

    if results:
        send_report(results)
    return results

def send_report(results):
    subject = "Price Tracker Report"
    html = """
    <html><body>
    <h3>Price Tracker Report</h3>
    <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse">
      <tr style="background:#f2f2f2"><th>Product</th><th>Current (₹)</th><th>Original (₹)</th><th>Discount (%)</th><th>Threshold (₹)</th><th>Status</th><th>Link</th></tr>
    """
    for r in results:
        html += f"<tr><td>{r['name']}</td><td>{r['current_price']}</td><td>{r['original_price']}</td><td>{r['discount']}</td><td>{r['threshold']}</td><td>{r['status']}</td><td><a href='{r['url']}'>view</a></td></tr>"
    html += "</table></body></html>"

    msg = MIMEMultipart("alternative")
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("Email sent.")
    except Exception as e:
        print("Failed to send email:", e)

# ---------- run loop ----------
if __name__ == "__main__":
    # quick sanity run
    asyncio.run(track_once())
    # To run periodically uncomment below:
    # while True:
    #     asyncio.run(track_once())
    #     time.sleep(CHECK_INTERVAL)
