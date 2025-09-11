import asyncio

from utils import playwright_price_scraper
from utils.common import console


def main() -> None:
    """Entry point for the price scraper."""
    console.print("Hello from price-scraper!")
    asyncio.run(playwright_price_scraper.main())


if __name__ == "__main__":
    main()
