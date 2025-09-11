# Price Tracker (Amazon + Flipkart)

A Python project using Playwright to track product prices on Amazon and Flipkart, 
send notifications, and generate reports.

## Features
- Track multiple products
- Detect discounts vs original price
- Email tabular reports
- Supports Amazon & Flipkart
- Proxy support (Tor)

## Setup
```bash
git clone https://github.com/username/price-tracker.git
cd price-tracker
uv sync
uv run playwright install

## Run
uv run python main.py