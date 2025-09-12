"""SQLite helpers for storing price history."""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("price_tracker.db")

def init_db() -> None:
    """Initialize the SQLite database and create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            url TEXT,
            platform TEXT,
            price REAL,
            threshold REAL,
            date TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_price(name: str, url: str, platform: str, price: float, threshold: float) -> None:
    """Save a price entry to the database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO price_history (name, url, platform, price, threshold, date)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, url, platform, price, threshold, datetime.now()))
    conn.commit()
    conn.close()

def get_latest_prices() -> list[tuple]:
    """Retrieve the latest price entries from the database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        SELECT name, price, threshold, date
        FROM price_history
        ORDER BY date DESC
    """)
    rows = c.fetchall()
    conn.close()
    return rows
