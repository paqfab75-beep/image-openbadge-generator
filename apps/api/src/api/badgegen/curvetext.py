"""Text on an arc, for the ring-placed title and the project name around the badge.

Each glyph is rendered into its own tile in the text color, rotated so it follows the circle, and
composited at its angular position on the transparent canvas. Image coordinates put y down: the
circle's top sits at angle -90°, its bottom at +90°. Top-arc text has its tops pointing outward;
bottom-arc text reads left to right with its tops toward the center, as on a seal.
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw, ImageFont


def _glyph_tile(char: str, font: ImageFont.FreeTypeFont, color: tuple[int, ...]) -> Image.Image | None:
    bbox = font.getmask(char).getbbox()
    if not bbox or bbox[2] == bbox[0] or bbox[3] == bbox[1]:
        return None
    width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tile = Image.new("RGBA", (width + 8, height + 8), (0, 0, 0, 0))
    tinted = Image.new("RGBA", tile.size, (*color[:3], 255))
    mask = Image.new("L", tile.size, 0)
    ImageDraw.Draw(mask).text((4 - bbox[0], 4 - bbox[1]), char, font=font, fill=255)
    tile.paste(tinted, (0, 0), mask)
    return tile


def _char_angle(char: str, font: ImageFont.FreeTypeFont, radius: float, tracking: float) -> float:
    bbox = font.getmask(char).getbbox()
    width = bbox[2] - bbox[0] if bbox else 0
    return (width + tracking) / radius


def arc_text(
    canvas: Image.Image,
    text: str,
    *,
    center: tuple[int, int],
    radius: float,
    font: ImageFont.FreeTypeFont,
    color: tuple[int, int, int],
    arc: str,
    max_angle: float = math.pi * 1.5,
) -> bool:
    """Write ``text`` centered on the arc. Answers False — before drawing anything — when the run
    is too wide for ``max_angle``, so the caller can shrink the font and retry."""
    tracking = font.size * 0.08
    angles = [_char_angle(char, font, radius, tracking) for char in text]
    total = sum(angles)
    if total > max_angle or total <= 0:
        return False

    if arc == "top":
        start, direction = -math.pi / 2 - total / 2, 1
    else:
        start, direction = math.pi / 2 + total / 2, -1

    angle = start
    for char, advance in zip(text, angles, strict=True):
        angle += direction * advance / 2
        glyph = _glyph_tile(char, font, color)
        if glyph is not None:
            # Bottom-arc glyphs host their tops toward the center, so their ink grows outward from
            # the baseline; halve the radius by the ink extent to keep the run inside the medallion.
            glyph_radius = radius - glyph.height / 2 if arc == "bottom" else radius
            position = (center[0] + glyph_radius * math.cos(angle), center[1] + glyph_radius * math.sin(angle))
            tilt = -(angle + math.pi / 2) if arc == "top" else (math.pi / 2 - angle)
            rotated = glyph.rotate(
                math.degrees(tilt),
                expand=True,
                resample=Image.Resampling.BICUBIC,
            )
            canvas.alpha_composite(
                rotated,
                (round(position[0] - rotated.width / 2), round(position[1] - rotated.height / 2)),
            )
        angle += direction * advance / 2
    return True
