#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import load_settings  # noqa: E402
from app.display import PortfolioDisplay  # noqa: E402
from app.portfolio import PortfolioSummary  # noqa: E402


def main() -> None:
    preview_path = Path("/tmp/snaptrade-display-test.png")
    settings = load_settings()
    display = PortfolioDisplay(
        preview_path,
        rotation=settings.display_rotation,
        theme=settings.display_theme,
    )
    result = display.render_connected(
        PortfolioSummary(
            total=Decimal("124382.16"),
            currency="USD",
            partial=False,
            skipped_items=0,
        ),
        updated_at=datetime.now(),
    )

    if result.hardware_updated:
        print("Display updated. You should see the SnapTrade test portfolio on the e-paper screen.")
    else:
        print("Preview rendered, but Waveshare hardware driver was not loaded.")
        print(f"Preview path: {result.preview_path}")


if __name__ == "__main__":
    main()
