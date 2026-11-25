"""Palette helpers: ordering, contrast, and darkening for borders and text."""

from __future__ import annotations

import colorsys
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class Palette:
    primary: tuple[int, int, int]
    accent: tuple[int, int, int]
    text: tuple[int, int, int]

    @classmethod
    def from_colors(cls, colors: list[str]) -> Self:
        """The charte of the form: first color is the body, the second (or a darker spin of it) borders,
        and text is the hue with the strongest contrast against the body."""
        primary = hex_to_rgb(colors[0])
        accent = hex_to_rgb(colors[1]) if len(colors) > 1 else scale(primary, 0.72)
        body_luma = luma(primary)
        text = max(
            (hex_to_rgb(c) for c in colors[2:]),
            key=lambda c: abs(luma(c) - body_luma),
            default=(255, 255, 255) if body_luma < 140 else (17, 17, 17),
        )
        if luma(text) > body_luma - 40 and luma(text) < body_luma + 40:
            text = (255, 255, 255) if body_luma < 140 else (17, 17, 17)
        return cls(primary=primary, accent=accent, text=text)


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))  # type: ignore[return-value]


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


def scale(rgb: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return tuple(min(255, max(0, round(channel * factor))) for channel in rgb)  # type: ignore[return-value]


def luma(rgb: tuple[int, int, int]) -> float:
    r, g, b = (channel / 255 for channel in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def harmonize_frequency(hue: float, count: int, steps: int = 5) -> tuple[int, int, int]:
    """A tint in the same hue family, used when the charte gives a single color."""
    sat, light = (0.62, 0.34) if count == 0 else (0.75, 0.2 + 0.12 * count / steps)
    return tuple(round(channel * 255) for channel in colorsys.hls_to_rgb(hue, light, sat))  # type: ignore[return-value]
