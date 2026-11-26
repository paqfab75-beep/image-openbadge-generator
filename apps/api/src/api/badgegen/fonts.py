"""The bundled DejaVu faces, the only text sources the render needs — the runtime image has none.

The TTFs live in the repository as base64 twins (``.ttf.b64``) because git content pushes carry
text only; the first load decodes them into a cache directory and every render reuses that.
"""

import base64
import os
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

_FONTS = Path(__file__).resolve().parent / "fonts"
_CACHE = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))) / "openbadge-fonts"


def _font_path(name: str) -> Path:
    ttf = _FONTS / name
    if ttf.exists():
        return ttf
    encoded = _FONTS / f"{name}.b64"
    if not encoded.exists():
        raise FileNotFoundError(f"Police absente du dépôt : {name} (ni .ttf ni .b64)")
    _CACHE.mkdir(parents=True, exist_ok=True)
    target = _CACHE / name
    if not target.exists():
        target.write_bytes(base64.b64decode(encoded.read_text().strip()))
    return target


@lru_cache(maxsize=32)
def _face(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(_font_path(name)), size)


def bold(size: int) -> ImageFont.FreeTypeFont:
    return _face("DejaVuSans-Bold.ttf", size)


def regular(size: int) -> ImageFont.FreeTypeFont:
    return _face("DejaVuSans.ttf", size)


class GlyphCoverageError(ValueError):
    """Raised when a picto character needs a font outside the bundled DejaVu set."""

    def __init__(self, char: str) -> None:
        self.char = char
        super().__init__(
            f"Le caractère {char!r} n'entre pas dans la police DejaVu intégrée ; "
            "utilisez un pictogramme de la liste ou un caractère imprimable simple."
        )


def check_glyph(char: str) -> None:
    """Fail early, before any drawing, on a non-whitespace character DejaVu cannot print."""
    if char.isspace():
        return
    font = regular(40)
    if font.getmask(char).getbbox() is None:
        raise GlyphCoverageError(char)
