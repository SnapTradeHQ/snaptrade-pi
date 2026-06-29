from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import qrcode
from PIL import Image, ImageDraw, ImageFont

from app.portfolio import PortfolioSummary, format_money


WIDTH = 250
HEIGHT = 122


@dataclass(frozen=True)
class DisplayRenderResult:
    preview_path: Path
    hardware_updated: bool


class PortfolioDisplay:
    def __init__(self, preview_path: Path, rotation: int = 0) -> None:
        self.preview_path = preview_path
        self.rotation = rotation
        self.hardware = self._load_waveshare()

    def render_boot(self, message: str = "Booting") -> DisplayRenderResult:
        return self._render(lambda draw: self._center_text(draw, "SnapTrade", message))

    def render_wifi_unavailable(self) -> DisplayRenderResult:
        return self._render(lambda draw: self._center_text(draw, "Wi-Fi unavailable", "Check setup"))

    def render_fetching(self) -> DisplayRenderResult:
        return self._render(lambda draw: self._center_text(draw, "SnapTrade", "Fetching portfolio"))

    def render_pairing(self, verification_uri_complete: str, user_code: str) -> DisplayRenderResult:
        def draw_pairing(draw: ImageDraw.ImageDraw) -> None:
            self._text(draw, (8, 6), "Connect SnapTrade", size=15)
            qr = qrcode.make(verification_uri_complete).resize((70, 70))
            draw.bitmap((8, 34), qr.convert("1"), fill=0)
            self._text(draw, (88, 34), "Scan or enter:", size=12)
            self._text(draw, (88, 54), user_code, size=22)
            self._text(draw, (88, 86), "Waiting for approval", size=12)

        return self._render(draw_pairing)

    def render_connected(
        self,
        summary: PortfolioSummary,
        updated_at: datetime,
        stale: bool = False,
        error_message: str | None = None,
    ) -> DisplayRenderResult:
        def draw_connected(draw: ImageDraw.ImageDraw) -> None:
            label = "Total Assets"
            self._centered_text(draw, 8, label, size=13, bold=True)

            amount = self._format_display_amount(summary.total, summary.currency)
            amount_font = self._fit_font(amount, max_width=238, max_size=42, min_size=24, bold=True)
            amount_box = draw.textbbox((0, 0), amount, font=amount_font)
            amount_width = amount_box[2] - amount_box[0]
            draw.text(
                ((WIDTH - amount_width) / 2, 36 - amount_box[1]),
                amount,
                font=amount_font,
                fill=0,
            )

            footer_parts = [f"Updated {updated_at.strftime('%-I:%M %p')}"]
            if summary.partial:
                footer_parts.append("partial")
            if stale:
                footer_parts.append("stale")
            footer = " · ".join(footer_parts)
            if stale and error_message:
                footer = f"{footer} · {error_message[:18]}"
            footer_font = self._fit_font(footer, max_width=238, max_size=12, min_size=9)
            footer_box = draw.textbbox((0, 0), footer, font=footer_font)
            footer_width = footer_box[2] - footer_box[0]
            draw.text(
                ((WIDTH - footer_width) / 2, HEIGHT - 18 - footer_box[1]),
                footer,
                font=footer_font,
                fill=0,
            )

        return self._render(draw_connected)

    def render_reconnect_needed(self) -> DisplayRenderResult:
        return self._render(lambda draw: self._center_text(draw, "Reconnect needed", "Start pairing again"))

    def _render(self, draw_fn) -> DisplayRenderResult:
        image = Image.new("1", (WIDTH, HEIGHT), 255)
        draw = ImageDraw.Draw(image)
        draw_fn(draw)
        if self.rotation == 180:
            image = image.rotate(180)
        self.preview_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(self.preview_path)
        hardware_updated = self._push_to_hardware(image)
        return DisplayRenderResult(self.preview_path, hardware_updated)

    def _push_to_hardware(self, image: Image.Image) -> bool:
        if self.hardware is None:
            return False
        epd = self.hardware
        if hasattr(epd, "FULL_UPDATE"):
            epd.init(epd.FULL_UPDATE)
        else:
            epd.init()
        epd.display(epd.getbuffer(image))
        epd.sleep()
        return True

    @staticmethod
    def _load_waveshare():
        try:
            from waveshare_epd import epd2in13_V4  # type: ignore

            return epd2in13_V4.EPD()
        except Exception:
            return None

    @staticmethod
    def _format_display_amount(value: Decimal, currency: str) -> str:
        if currency == "USD":
            rounded = value.quantize(Decimal("1"))
            return f"${rounded:,.0f}"
        return format_money(value, currency)

    @staticmethod
    def _font(size: int, bold: bool = False) -> ImageFont.ImageFont:
        candidates = (
            [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            ]
            if bold
            else [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/System/Library/Fonts/Supplemental/Arial.ttf",
            ]
        )
        for path in candidates:
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
        try:
            return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)
        except OSError:
            return ImageFont.load_default()

    def _fit_font(
        self,
        text: str,
        max_width: int,
        max_size: int,
        min_size: int,
        bold: bool = False,
    ) -> ImageFont.ImageFont:
        scratch = Image.new("1", (WIDTH, HEIGHT), 255)
        draw = ImageDraw.Draw(scratch)
        for size in range(max_size, min_size - 1, -1):
            font = self._font(size, bold=bold)
            box = draw.textbbox((0, 0), text, font=font)
            if box[2] - box[0] <= max_width:
                return font
        return self._font(min_size, bold=bold)

    def _text(self, draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, size: int) -> None:
        draw.text(xy, text, font=self._font(size), fill=0)

    def _centered_text(
        self,
        draw: ImageDraw.ImageDraw,
        y: int,
        text: str,
        size: int,
        bold: bool = False,
    ) -> None:
        font = self._font(size, bold=bold)
        box = draw.textbbox((0, 0), text, font=font)
        draw.text(((WIDTH - (box[2] - box[0])) / 2, y - box[1]), text, font=font, fill=0)

    def _center_text(self, draw: ImageDraw.ImageDraw, title: str, subtitle: str) -> None:
        title_font = self._font(18)
        subtitle_font = self._font(13)
        title_box = draw.textbbox((0, 0), title, font=title_font)
        subtitle_box = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        draw.text(((WIDTH - (title_box[2] - title_box[0])) / 2, 38), title, font=title_font, fill=0)
        draw.text(
            ((WIDTH - (subtitle_box[2] - subtitle_box[0])) / 2, 67),
            subtitle,
            font=subtitle_font,
            fill=0,
        )
