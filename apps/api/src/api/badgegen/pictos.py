"""The drawable pictograms: named vector glyphs plus single printable characters.

Each glyph draws in a square ``box`` with its stroke color, in sRGB coordinates where the whole
canvas is 1000. Named pictos keep lines thick enough to survive a small badge print.
"""

from __future__ import annotations

import math
from collections.abc import Callable

from PIL import Image, ImageDraw

Glyph = Callable[[ImageDraw.ImageDraw, tuple[int, int, int, int], tuple[int, int, int]], None]


def _star(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    radius, inner = (x1 - x0) / 2, (x1 - x0) / 4.6
    points = []
    for i in range(10):
        r = radius if i % 2 == 0 else inner
        angle = -math.pi / 2 + i * math.pi / 5
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(points, fill=color)


def _check(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = box
    w = (x1 - x0) * 0.16
    draw.line([(x0 + 0.12 * (x1 - x0), y0 + 0.52 * (y1 - y0)), (x0 + 0.42 * (x1 - x0), y0 + 0.82 * (y1 - y0))], fill=color, width=round(w))
    draw.line([(x0 + 0.42 * (x1 - x0), y0 + 0.82 * (y1 - y0)), (x0 + 0.9 * (x1 - x0), y0 + 0.16 * (y1 - y0))], fill=color, width=round(w))


def _medal(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    band_w = w * 0.26
    draw.polygon([(x0 + 0.24 * w, y0), (x0 + 0.24 * w, y0 + 0.38 * h), (x0 + 0.24 * w + band_w, y0 + 0.38 * h), (x0 + 0.24 * w + band_w, y0)], fill=color)
    draw.polygon([(x0 + 0.5 * w + 0.0 * w, y0), (x0 + 0.5 * w, y0 + 0.38 * h), (x0 + 0.5 * w + band_w, y0 + 0.38 * h), (x0 + 0.5 * w + band_w, y0)], fill=color)
    cy, r = y0 + 0.66 * h, w * 0.3
    draw.ellipse([w / 2 - r, cy - r, w / 2 + r, cy + r], outline=color, width=round(w * 0.09))
    _star(draw, (w / 2 - r * 0.72, cy - r * 0.62, w / 2 + r * 0.72, cy + r * 0.72), color)


def _trophy(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    draw.rounded_rectangle([x0 + 0.18 * w, y0, x0 + 0.82 * w, y0 + 0.5 * h], radius=w * 0.1, outline=color, width=round(w * 0.08))
    draw.arc([x0 - 0.18 * w, y0 + 0.06 * h, x0 + 0.42 * w, y0 + 0.6 * h], start=90, end=270, fill=color, width=round(w * 0.08))
    draw.arc([x0 + 0.58 * w, y0 + 0.06 * h, x1 + 0.18 * w, y0 + 0.6 * h], start=270, end=450, fill=color, width=round(w * 0.08))
    draw.line([(w / 2, y0 + 0.5 * h), (w / 2, y0 + 0.76 * h)], fill=color, width=round(w * 0.1))
    draw.line([(x0 + 0.26 * w, y0 + 0.88 * h), (x0 + 0.74 * w, y0 + 0.88 * h)], fill=color, width=round(w * 0.12))


def _gear(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    radius, thickness = (x1 - x0) / 2, (x1 - x0) * 0.17
    for i in range(8):
        a = i * math.pi / 4
        draw.line(
            [(cx + (radius - thickness) * math.cos(a), cy + (radius - thickness) * math.sin(a)), (cx + radius * math.cos(a), cy + radius * math.sin(a))],
            fill=color,
            width=round(thickness * 1.15),
        )
    draw.ellipse([cx - radius + thickness, cy - radius + thickness, cx + radius - thickness, cy + radius - thickness], outline=color, width=round(thickness))
    hole = thickness * 0.9
    draw.ellipse([cx - hole, cy - hole, cx + hole, cy + hole], fill=color)


def _flag(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    draw.line([(x0 + 0.14 * w, y0), (x0 + 0.14 * w, y1)], fill=color, width=round(w * 0.1))
    draw.polygon([(x0 + 0.2 * w, y0 + 0.08 * h), (x1, y0 + 0.3 * h), (x0 + 0.2 * w, y0 + 0.52 * h)], fill=color)


def _book(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    mid = x0 + w / 2
    draw.polygon([(mid, y0 + 0.18 * h), (mid, y0 + 0.92 * h), (x0, y1), (x0, y0 + 0.26 * h)], outline=color, width=round(w * 0.08))
    draw.polygon([(mid, y0 + 0.18 * h), (mid, y0 + 0.92 * h), (x1, y1), (x1, y0 + 0.26 * h)], outline=color, width=round(w * 0.08))


def _certificate(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], color: tuple[int, int, int]) -> None:
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    draw.rounded_rectangle([x0, y0, x1, y0 + 0.72 * h], radius=w * 0.06, outline=color, width=round(w * 0.07))
    for i, frac in enumerate((0.3, 0.45)):
        draw.line([(x0 + 0.18 * w, y0 + frac * h), (x1 - (0.32 if i == 0 else 0.18) * w, y0 + frac * h)], fill=color, width=round(w * 0.055))
    _medal(draw, (x1 - 0.42 * w, y0 + 0.5 * h, x1 - 0.06 * w, y1), color)


VECTORS: dict[str, Glyph] = {
    "star": _star,
    "check": _check,
    "medal": _medal,
    "trophy": _trophy,
    "gear": _gear,
    "flag": _flag,
    "book": _book,
    "certificate": _certificate,
}


def known_pictos() -> list[str]:
    return sorted(VECTORS)


def draw_picto(canvas: Image.Image, code: str, box: tuple[float, float, float, float], color: tuple[int, int, int]) -> None:
    draw = ImageDraw.Draw(canvas)
    box_px = tuple(int(round(c)) for c in box)
    glyph = VECTORS.get(code.strip().lower())
    if glyph is not None:
        glyph(draw, box_px, color)
        return

    from api.badgegen import fonts

    fonts.check_glyph(code)
    size = int(min(box[2] - box[0], box[3] - box[1])) * 2
    font = fonts.regular(size)
    left, top, right, bottom = draw.textbbox((0, 0), code, font=font)
    glyph_w, glyph_h = right - left, bottom - top
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    draw.text((cx - glyph_w / 2 - left, cy - glyph_h / 2 - top), code, font=font, fill=color)
