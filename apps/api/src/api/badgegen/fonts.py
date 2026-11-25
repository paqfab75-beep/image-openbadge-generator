"""The bundled DejaVu faces, the only text sources the render needs — the runtime image has none."""

from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

_FONTS = Path(__file__).resolve().parent / "fonts"


@lru_cache(maxsize=32)
def _face(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(_FONTS / name), size)


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
