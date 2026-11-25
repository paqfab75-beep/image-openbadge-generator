"""The badge render: a square 1000×1000 canvas, a shape-clipped medallion, the title, the pictos,
the project name on an arc, and a PNG encoder that answers at or under the 250 KiB Open Badges cap.
"""

from __future__ import annotations

import base64
import binascii
import io
import math
import re

from PIL import Image, ImageDraw, ImageFont, ImageOps

from api.badgegen import colors as colors_module
from api.badgegen import curvetext, fonts, pictos
from api.badgegen.models import MAX_PNG_BYTES, SIZE, BadgeSpec

SHAPE_POINTS = {
    "diamond": 4,
    "hexagon": 6,
}

HexPattern = re.compile(r"#[0-9a-fA-F]{6}")


class BackgroundImageError(ValueError):
    """Raised when the uploaded background is not a decodable raster image."""


def _shape_bbox(shape: str) -> tuple[int, int, int, int]:
    """The medallion's extent on the square canvas; squares use more of the width than circles."""
    if shape == "circle":
        inset = 70
    elif shape in SHAPE_POINTS:
        inset = 90
    else:
        inset = 40
    return (inset, inset, SIZE - inset, SIZE - inset)


def _shape_polygon(shape: str, box: tuple[int, int, int, int]) -> list[tuple[float, float]]:
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = (x1 - x0) / 2, (y1 - y0) / 2
    if shape == "diamond":
        return [(cx, y0), (x1, cy), (cx, y1), (x0, cy)]
    sides = SHAPE_POINTS.get(shape, 6)
    if shape == "hexagon":
        return [(cx + dx * math.cos(a), cy + dy * math.sin(a)) for a in
                (i * 2 * math.pi / sides - math.pi / 2 for i in range(sides))]
    return []


def _shape_mask(shape: str, box: tuple[int, int, int, int]) -> Image.Image:
    mask = Image.new("L", (SIZE, SIZE), 0)
    draw = ImageDraw.Draw(mask)
    if shape == "circle":
        draw.ellipse(box, fill=255)
    elif shape == "rounded_square":
        draw.rounded_rectangle(box, radius=(box[2] - box[0]) * 0.12, fill=255)
    elif shape == "square":
        draw.rectangle(box, fill=255)
    else:
        draw.polygon(_shape_polygon(shape, box), fill=255)
    return mask


def _resize_cover(image: Image.Image) -> Image.Image:
    return ImageOps.fit(image.convert("RGBA"), (SIZE, SIZE), Image.Resampling.LANCZOS)


def _decode_background(spec: BadgeSpec) -> Image.Image | None:
    if not spec.background_image_b64:
        return None
    try:
        raw = base64.b64decode(spec.background_image_b64, validate=True)
        image = Image.open(io.BytesIO(raw))
        image.load()
    except (binascii.Error, ValueError, Image.DecompressionBombError, OSError) as error:
        raise BackgroundImageError("L'image de fond n'est pas un fichier image lisible.") from error
    return _resize_cover(image)


def _base_canvas(spec: BadgeSpec, background: Image.Image | None) -> Image.Image:
    if background is not None:
        canvas = background.copy()
    elif spec.background_color:
        canvas = Image.new("RGBA", (SIZE, SIZE), (*colors_module.hex_to_rgb(spec.background_color), 255))
    else:
        canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    return canvas


def _fit_font(text: str, box_w: int, box_h: int, start: int, *, bold: bool, lines: int = 1) -> ImageFont.FreeTypeFont:
    load = fonts.bold if bold else fonts.regular
    for size in range(start, 18, -4):
        font = load(size)
        left, top, right, bottom = font.getbbox(text)
        if right - left <= box_w and (bottom - top) * lines <= box_h:
            return font
    return load(18)


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if font.getlength(candidate) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_centered_block(draw: ImageDraw.ImageDraw, lines: list[str], font: ImageFont.FreeTypeFont, color, cy: int) -> None:
    line_h = font.size * 1.18
    top = cy - line_h * len(lines) / 2
    for i, line in enumerate(lines):
        left, top_line, right, bottom = draw.textbbox((0, 0), line, font=font)
        draw.text((SIZE / 2 - (right - left) / 2 - left, top + i * line_h - top_line), line, font=font, fill=color)


def _medallion(spec: BadgeSpec, palette: colors_module.Palette) -> Image.Image:
    """The badge body: the shape filled with the primary color, lined with the accent, on a
    transparent layer that the canvas builder composites at the end."""
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    box = _shape_bbox(spec.shape)
    draw = ImageDraw.Draw(layer)
    fill = (*palette.primary, 255)

    if spec.shape == "circle":
        draw.ellipse(box, fill=fill, outline=(*palette.accent, 255), width=18)
        inner = (box[0] + 34, box[1] + 34, box[2] - 34, box[3] - 34)
        draw.ellipse(inner, outline=(*palette.accent, 200), width=4)
    elif spec.shape in ("square", "rounded_square"):
        radius = (box[2] - box[0]) * 0.12 if spec.shape == "rounded_square" else 0
        draw.rounded_rectangle(box, radius=radius, fill=fill, outline=(*palette.accent, 255), width=18)
        inner = (box[0] + 32, box[1] + 32, box[2] - 32, box[3] - 32)
        draw.rounded_rectangle(inner, radius=radius * 0.6, outline=(*palette.accent, 200), width=4)
    else:
        polygon = _shape_polygon(spec.shape, box)
        draw.polygon(polygon, fill=fill, outline=(*palette.accent, 255), width=16)

    return layer


def _apply_mask(target: Image.Image, shape: str, box: tuple[int, int, int, int]) -> Image.Image:
    """Everything drawn on the medallion stays inside the shape, hard edge included."""
    layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    layer.alpha_composite(target)
    layer.putalpha(Image.composite(layer.split()[3], Image.new("L", (SIZE, SIZE), 0), _shape_mask(shape, box)))
    return layer


def render(spec: BadgeSpec) -> tuple[Image.Image, bytes]:
    palette = colors_module.Palette.from_colors(spec.colors) if spec.colors else colors_module.Palette(
        primary=(28, 84, 158), accent=(240, 180, 41), text=(255, 255, 255)
    )
    for char in (spec.project_name or "") + "".join(p for p in spec.pictos if p not in pictos.VECTORS):
        fonts.check_glyph(char)

    background = _decode_background(spec)
    canvas = _base_canvas(spec, background)
    medallion = _medallion(spec, palette)
    inner = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    inner.alpha_composite(medallion)

    _draw_inner_content(inner, spec, palette)
    inner = _apply_mask(inner, spec.shape, _shape_bbox(spec.shape))
    canvas.alpha_composite(inner)
    return canvas, _encode(canvas)


def _draw_inner_content(layer: Image.Image, spec: BadgeSpec, palette: colors_module.Palette) -> None:
    draw = ImageDraw.Draw(layer)
    center = (SIZE // 2, SIZE // 2)
    text_color = (*palette.text, 255)
    picto_color = (*palette.accent, 255) if colors_module.luma(palette.accent) > 0.12 else (*palette.text, 255)

    title_on_arc = spec.title_placement == "ring"
    title_font = fonts.bold(64 if title_on_arc else 120)

    arcs_top: list[str] = []
    arcs_bottom: list[str] = []
    project = (spec.project_name or "").strip()
    title = spec.title.strip()

    if title_on_arc:
        arcs_top.append(title)
        if project and spec.project_position == "bottom":
            arcs_bottom.append(project)
        elif project:
            arcs_bottom.append(project)
    if project and not title_on_arc:
        (arcs_top if spec.project_position == "top" else arcs_bottom).append(project)

    box = _shape_bbox(spec.shape)
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    # The arc sits on the largest circle every point of the shape contains: the polygon vertices
    # pinch the inscribed circle far inward, so polygon shapes get a notably smaller radius.
    arc_radii = {"circle": (box[2] - box[0]) / 2 - 62, "hexagon": 318, "diamond": 243}
    radius = arc_radii.get(spec.shape, 330)

    if spec.shape in ("square", "rounded_square"):
        for arc, items in (("top", arcs_top), ("bottom", arcs_bottom)):
            for text in items:
                y = box[1] + 92 if arc == "top" else box[3] - 92
                _edge_text(draw, text, text_color, box, y)
    else:
        shape_mask = _shape_mask(spec.shape, box)
        for arc, items in (("top", arcs_top), ("bottom", arcs_bottom)):
            for text in items:
                placed = _place_arc_text(layer, text, shape_mask, center=(round(cx), round(cy)),
                                         radius=radius, arc=arc, color=text_color)
                if not placed:
                    raise ValueError(f"Le texte « {text} » est trop long pour tenir sur le pourtour du badge.")

    if title_on_arc:
        picto_row_y = cy - 40
    elif spec.title_placement == "center":
        picto_row_y = cy - 250 if spec.pictos else None
    elif spec.title_placement == "top":
        picto_row_y = cy - 40
    else:
        picto_row_y = None

    if spec.pictos and picto_row_y is not None:
        _draw_picto_row(layer, spec.pictos, picto_color, center_x=round(cx), cy=round(picto_row_y), size=110)

    if not title_on_arc:
        if spec.title_placement == "center":
            lines, row_shift = _title_lines(spec.title, title_font, box), max(40, 90 if spec.pictos else 0)
            _draw_centered_block(draw, lines, title_font, text_color, round(cy + row_shift))
        elif spec.title_placement == "top":
            lines = _title_lines(spec.title, title_font, box)
            _draw_centered_block(draw, lines, title_font, text_color, round(box[1] + 190))
        else:
            lines = _title_lines(spec.title, title_font, box)
            _draw_centered_block(draw, lines, title_font, text_color, round(box[3] - 190))


def _place_arc_text(
    layer: Image.Image,
    text: str,
    shape_mask: Image.Image,
    *,
    center: tuple[int, int],
    radius: float,
    arc: str,
    color,
) -> bool:
    """Try a shrinking font; keep only a run whose every inked pixel stays inside the shape."""
    from PIL import ImageChops

    for size in range(84, 22, -4):
        scratch = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        if not curvetext.arc_text(
            scratch, text, center=center, radius=radius, arc=arc, font=fonts.bold(size), color=color,
            max_angle=math.radians(110),
        ):
            continue
        spilled = ImageChops.multiply(scratch.split()[3], ImageChops.invert(shape_mask))
        if spilled.getbbox() is None:
            layer.alpha_composite(scratch)
            return True
    return False


def _edge_text(draw: ImageDraw.ImageDraw, text: str, color, box: tuple[int, int, int, int], y: int) -> None:
    """Ring text for the square shapes: one horizontal line hugging the top or bottom edge."""
    font = fonts.bold(72)
    while font.size > 24 and font.getlength(text) > (box[2] - box[0]) * 0.8:
        font = fonts.bold(font.size - 6)
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    draw.text((SIZE / 2 - (right - left) / 2 - left, y - (bottom - top) / 2 - top), text, font=font, fill=color)


def _title_lines(title: str, font: ImageFont.FreeTypeFont, box: tuple[int, int, int, int]) -> list[str]:
    return _wrap(title, font, int((box[2] - box[0]) * 0.74))


def _draw_picto_row(layer: Image.Image, codes: list[str], color, center_x: int, cy: int, size: int) -> None:
    gap = 56
    total = len(codes) * size + (len(codes) - 1) * gap
    x = center_x - total / 2
    for code in codes:
        pictos.draw_picto(layer, code, (x, cy - size / 2, x + size, cy + size / 2), color)
        x += size + gap


def _encode(canvas: Image.Image) -> bytes:
    """PNG with alpha, at or under 250 KiB: optimize first, then adaptive palettes."""
    for palette_size in (None, 256, 128, 64, 32, 16):
        png = _encode_once(canvas, palette_size)
        if len(png) <= MAX_PNG_BYTES:
            return png
    raise ValueError("Impossible d'atteindre 250 Ko pour cette image de fond ; réduisez sa complexité.")


def _encode_once(canvas: Image.Image, palette_size: int | None) -> bytes:
    image = canvas if palette_size is None else canvas.quantize(colors=palette_size, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.FS)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True, compress_level=9)
    return buffer.getvalue()
