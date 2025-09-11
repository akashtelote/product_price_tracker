from utils import playwright_price_scraper
import asyncio

def main():
    print("Hello from price-scraper!")
    asyncio.run(playwright_price_scraper.main())


if __name__ == "__main__":
    main()
