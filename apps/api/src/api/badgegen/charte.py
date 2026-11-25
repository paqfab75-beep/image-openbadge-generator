"""Charte extraction: dominant colors from a PDF's pages, or from a reference website.

The answer is a short palette of ``#rrggbb`` colors, most frequent first, to prefill the form's
color zones. The user keeps the last word: picked colors edit or replace whatever this proposes.
"""

from __future__ import annotations

import re
from collections import Counter
from io import BytesIO

import httpx
from PIL import Image

MAX_PDF_BYTES = 4 * 1024 * 1024
MAX_URL_BYTES = 3 * 1024 * 1024


class CharteExtractionError(ValueError):
    """Raised when neither source yields a usable palette."""


def extract_from_pdf(raw: bytes, *, pages: int = 3) -> list[str]:
    """Render the first pages at a small scale and count quantized pixel colors."""
    import pypdfium2 as pdfium

    try:
        document = pdfium.PdfDocument(BytesIO(raw))
    except Exception as error:  # pypdfium2 raises assorted native-backed errors
        raise CharteExtractionError("Le PDF de la charte est illisible.") from error

    pixels: Counter[tuple[int, int, int]] = Counter()
    with document:
        for index, page in enumerate(document):
            if index >= pages:
                break
            image = page.render(scale=0.5).to_pil().convert("RGB")
            dominant = image.quantize(colors=8).convert("RGB").getcolors(maxcolors=9) or []
            for count, color in dominant:
                pixels[color] += count
    return _top_colors(pixels)


def extract_from_url(url: str, *, timeout: float = 12.0) -> list[str]:
    """Fetch the page's HTML and stylesheets and count the colors they declare."""
    response = httpx.get(
        url,
        timeout=timeout,
        follow_redirects=True,
        headers={"User-Agent": "openbadge-generator/1.0"},
    )
    response.raise_for_status()
    body = response.text[:MAX_URL_BYTES]

    from api.badgegen.colors import hex_to_rgb

    counter: Counter[tuple[int, int, int]] = Counter()
    for match in re.finditer(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", body):
        value = match.group(1)
        if len(value) == 3:
            value = "".join(char * 2 for char in value)
        rgb = hex_to_rgb("#" + value)
        if rgb not in ((0, 0, 0), (255, 255, 255)):
            counter[rgb] += 1
    for match in re.finditer(r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})", body):
        rgb = tuple(int(channel) for channel in match.groups())  # type: ignore[assignment]
        if rgb not in ((0, 0, 0), (255, 255, 255)):
            counter[rgb] += 1  # type: ignore[unreachable]
    return _top_colors(counter)


def _top_colors(counts: Counter[tuple[int, int, int]], wanted: int = 6) -> list[str]:
    from api.badgegen.colors import rgb_to_hex

    palette: list[tuple[int, int, int]] = []
    for color, _ in counts.most_common(200):
        if palette and all(max(abs(a - b) for a, b in zip(color, kept)) < 24 for kept in palette):
            continue
        palette.append(color)
        if len(palette) >= wanted:
            break
    if not palette:
        raise CharteExtractionError("Aucune couleur exploitable n'a été trouvée.")
    return [rgb_to_hex(color) for color in palette]
