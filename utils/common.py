# utils/common.py
"""Shared Rich console for pretty output across the project."""

# ruff: noqa: BLE001

import traceback
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from rich.console import Console
from rich.table import Table

console = Console()

P = ParamSpec("P")
R = TypeVar("R")

def safe_run(func: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R | None:
    """Run a function safely.

    Returns the result of the function or None if any error occurs.

    Exceptions are logged to the console with traceback.
    """
    try:
        return func(*args, **kwargs)
    except BaseException as e:  # Broad catch, safe fallback
        console.print("[red]Unexpected error:[/]", e)
        console.print(traceback.format_exc())
        return None

def display_price_table(results: list[dict]) -> None:
    """Display price tracker results in a Rich table.

    Each item in results should have:
    - name: str
    - current_price: float
    - original_price: float
    """
    table = Table(title="Price Tracker Results")

    table.add_column("Product", style="bold cyan", no_wrap=True)
    table.add_column("Current Price (₹)", justify="right", style="green")
    table.add_column("Original Price (₹)", justify="right", style="yellow")
    table.add_column("Discount (%)", justify="right", style="magenta")

    for item in results:
        name = item.get("name", "Unknown")
        current = item.get("current_price", 0)
        original = item.get("original_price", 0)
        discount = 0
        if original > 0:
            discount = round((original - current) / original * 100, 2)
        table.add_row(name, f"{current:.2f}", f"{original:.2f}", f"{discount:.2f}%")

    console.print(table)
