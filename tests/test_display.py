from datetime import datetime
from decimal import Decimal

from PIL import Image

from app.display import PortfolioDisplay
from app.portfolio import PortfolioSummary


def test_dark_theme_renders_black_background(tmp_path) -> None:
    preview_path = tmp_path / "dark.png"
    display = PortfolioDisplay(preview_path, theme="dark")

    display.render_connected(
        PortfolioSummary(
            total=Decimal("124382.16"),
            currency="USD",
            partial=False,
            skipped_items=0,
        ),
        updated_at=datetime(2026, 6, 29, 12, 30),
    )

    image = Image.open(preview_path)

    assert image.getpixel((0, 0)) == 0


def test_light_theme_renders_white_background(tmp_path) -> None:
    preview_path = tmp_path / "light.png"
    display = PortfolioDisplay(preview_path)

    display.render_connected(
        PortfolioSummary(
            total=Decimal("124382.16"),
            currency="USD",
            partial=False,
            skipped_items=0,
        ),
        updated_at=datetime(2026, 6, 29, 12, 30),
    )

    image = Image.open(preview_path)

    assert image.getpixel((0, 0)) == 255
