from decimal import Decimal

from app.portfolio import aggregate_portfolio, format_money


def test_aggregate_portfolio_sums_display_currency() -> None:
    summary = aggregate_portfolio(
        [
            {"value": "100.50", "currency": "USD"},
            {"marketValue": "20", "currency": "USD"},
            {"value": "10", "currency": "CAD"},
            {"value": None, "currency": "USD"},
        ],
        "USD",
    )

    assert summary.total == Decimal("120.50")
    assert summary.currency == "USD"
    assert summary.partial is True
    assert summary.skipped_items == 2


def test_aggregate_portfolio_includes_zero_values() -> None:
    summary = aggregate_portfolio(
        [
            {"value": 0, "currency": "USD"},
            {"marketValue": "0.00", "currency": "USD"},
        ],
        "USD",
    )

    assert summary.total == Decimal("0.00")
    assert summary.partial is False
    assert summary.skipped_items == 0


def test_format_money_usd() -> None:
    assert format_money(Decimal("124382.16"), "USD") == "$124,382.16"
