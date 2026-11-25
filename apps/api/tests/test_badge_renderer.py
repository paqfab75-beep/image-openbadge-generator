"""The badge render contract: a square PNG of exactly 1000×1000, at or under 250 KiB."""

import base64
import io

import pytest
from api.badgegen import renderer

from api.badgegen.models import BadgeSpec
from PIL import Image


def spec(**overrides) -> BadgeSpec:
    base = {
        "title": "Data Scientist",
        "shape": "circle",
        "pictos": ["star", "check"],
        "project_name": "Académie du numérique",
        "colors": ["#123a6d", "#f0b429"],
    }
    return BadgeSpec.model_validate({**base, **overrides})


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param(spec(), id="circle"),
        pytest.param(spec(shape="square", title_placement="ring"), id="square-ring"),
        pytest.param(spec(shape="rounded_square", title_placement="top"), id="rounded-top"),
        pytest.param(spec(shape="hexagon", title_placement="center", project_name=None), id="hexagon"),
        pytest.param(spec(shape="diamond", title_placement="bottom", pictos=["medal", "trophy", "book"]), id="diamond"),
        pytest.param(spec(colors=[], project_name=None, pictos=[]), id="defaults"),
        pytest.param(spec(colors=["#7b1fa2"]), id="one_color"),
    ],
)
def test_render_answers_the_open_badge_format(payload: BadgeSpec) -> None:
    _, png = renderer.render(payload)
    assert len(png) <= 250 * 1024
    image = Image.open(io.BytesIO(png))
    assert image.format == "PNG"
    assert image.size == (1000, 1000)


def test_a_circle_marks_corners_transparent() -> None:
    image, _ = renderer.render(spec())
    assert image.getpixel((5, 5))[3] == 0


def test_a_background_color_fills_the_square() -> None:
    image, _ = renderer.render(spec(background_color="#e9c46a"))
    assert image.getpixel((2, 2))[:3] == (233, 196, 106)


def test_a_background_image_is_fitted_not_stretched() -> None:
    raw = io.BytesIO()
    Image.new("RGB", (500, 2000), (10, 200, 30)).save(raw, format="PNG")
    image, _ = renderer.render(
        spec(background_image_b64=base64.b64encode(raw.getvalue()).decode("ascii"))
    )
    assert image.getpixel((500, 40))[:3] == (10, 200, 30)  # the square backdrop is the cover fit
    assert image.getpixel((2, 999))[:3] == (10, 200, 30)


def test_a_broken_background_image_is_refused() -> None:
    with pytest.raises(renderer.BackgroundImageError):
        renderer.render(spec(background_image_b64="aGVsbG8="))


def test_every_known_picto_draws() -> None:
    from api.badgegen.pictos import known_pictos

    for code in known_pictos():
        image, _ = renderer.render(spec(pictos=[code], shape="square", title_placement="bottom"))
        assert image.getbbox() is not None
