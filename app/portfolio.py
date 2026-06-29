from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass(frozen=True)
class PortfolioSummary:
    total: Decimal
    currency: str
    partial: bool
    skipped_items: int


def _decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def aggregate_portfolio(items: list[dict[str, Any]], display_currency: str) -> PortfolioSummary:
    total = Decimal("0")
    skipped = 0

    for item in items:
        currency = item.get("currency") or item.get("valueCurrency")
        raw_value = (
            item.get("value")
            or item.get("balance")
            or item.get("market_value")
            or item.get("marketValue")
        )
        value = _decimal(raw_value)
        if currency != display_currency or value is None:
            skipped += 1
            continue
        total += value

    return PortfolioSummary(
        total=total,
        currency=display_currency,
        partial=skipped > 0,
        skipped_items=skipped,
    )


def format_money(value: Decimal, currency: str) -> str:
    if currency == "USD":
        return f"${value:,.2f}"
    return f"{value:,.2f} {currency}"

