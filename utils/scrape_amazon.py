async def scrape_amazon(url, page) -> tuple[float, float] | None:
    try:
        await page.goto(url, wait_until="domcontentloaded")
        # Amazon current price
        price_el = await page.query_selector("span.a-price-whole")
        if not price_el:
            price_el = await page.query_selector("#priceblock_dealprice") or await page.query_selector("#priceblock_ourprice")
        price_text = (await price_el.inner_text()).replace(",", "").replace("\n", "").replace("₹", "").strip()

        current_price = float(price_text)

        # Amazon original price (strikethrough)
        original_el = await page.query_selector("span.a-text-price span.a-offscreen")
        if original_el:
            orig_text = (await original_el.inner_text()).replace(",", "").replace("\n", "").replace("₹", "").strip()
            original_price = float(orig_text)
        else:
            original_price = current_price
        return current_price, original_price
    except:
        return None    