"""The badge specification the form fills in, and what generation answers with."""

import re
from typing import Annotated, Literal

from pydantic import BaseModel, Field

SHAPE = Literal["circle", "square", "rounded_square", "hexagon", "diamond"]
TITLE_PLACEMENT = Literal["center", "top", "bottom", "ring"]
ARC = Literal["top", "bottom"]

HexColor = Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")]
"""A color as ``#rrggbb``. The form offers pickers and the charte extraction answers the same."""

Base64Bytes = Annotated[str, Field(max_length=6_000_000)]
"""One base64-encoded file, decoded size capped at 4 MiB."""

MAX_PNG_BYTES = 250 * 1024
SIZE = 1000


class BadgeSpec(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=80, description="Le titre du badge, imprimé sur l'image.")]
    title_placement: TITLE_PLACEMENT = Field(
        default="center",
        description="Où le titre se place : centré, en haut, en bas, ou en écriture incurvée sur le pourtour.",
    )
    shape: SHAPE = Field(default="circle", description="Forme du visuel : rond, carré, ou une autre forme.")
    pictos: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="De 0 à 3 pictogrammes, par code ('star', 'check', 'medal') ou un seul caractère "
        "imprimable (★, ✓…) repris tel quel.",
    )
    project_name: str | None = Field(
        default=None,
        max_length=80,
        description="Un nom de projet écrit autour du badge, sur l'arc haut ou bas.",
    )
    project_position: ARC = "bottom"
    colors: list[HexColor] = Field(default_factory=list, max_length=12, description="Les couleurs de la charte, du plus principal au plus secondaire.")
    background_color: HexColor | None = None
    background_image_b64: Base64Bytes | None = None


class CharteRequest(BaseModel):
    pdf_b64: Base64Bytes | None = None
    pdf_filename: str | None = Field(default=None, max_length=255)
    url: str | None = Field(default=None, max_length=2048)


class CharteResponse(BaseModel):
    colors: list[HexColor]


class GeneratedBadge(BaseModel):
    png_b64: str
    size_bytes: int = Field(description="Toujours ≤ 250 Ko.")
    width: int = SIZE
    height: int = SIZE


def is_valid_hex(value: str) -> bool:
    return re.fullmatch(r"#[0-9a-fA-F]{6}", value) is not None
