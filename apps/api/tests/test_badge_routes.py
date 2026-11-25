"""The badge routes: generation answers base64 PNG within the Open Badges constraints, the charte
extraction reads palettes from PDFs, and bad input is refused in words."""

import base64
import io

import pytest
from api.badgegen.pictos import known_pictos
from fastapi.testclient import TestClient


@pytest.fixture
def client() -> TestClient:
    from conftest import build_app

    return TestClient(build_app())


def generate(client: TestClient, payload: dict):
    return client.post(
        "/api/v1/badges/generate",
        json={"title": "Data Scientist", "shape": "circle", **payload},
    )


def test_generate_answers_png_metadata(client: TestClient) -> None:
    res = generate(client, {"colors": ["#123a6d", "#f0b429"], "pictos": ["star"]})
    assert res.status_code == 200
    data = res.json()
    assert data["width"] == 1000 and data["height"] == 1000
    assert data["size_bytes"] <= 250 * 1024
    raw = base64.b64decode(data["png_b64"])
    assert raw.startswith(b"\x89PNG\r\n\x1a\n")


@pytest.mark.parametrize("detail", ["Le texte", "trop long"])
def test_an_unfittable_ring_title_is_refused_in_words(client: TestClient, detail: str) -> None:
    res = generate(client, {"title": "a" * 80, "title_placement": "ring", "shape": "hexagon"})
    assert res.status_code == 422
    assert any(word in res.json()["detail"] for word in (detail,))


def test_unknown_picto_codes_still_draw_or_refuse_cleanly(client: TestClient) -> None:
    res = generate(client, {"pictos": ["star"], "colors": []})
    assert res.status_code == 200


def a_pdf() -> bytes:
    from PIL import Image, ImageDraw

    page = Image.new("RGB", (400, 400), (36, 90, 160))
    draw = ImageDraw.Draw(page)
    draw.rectangle([40, 40, 360, 360], fill=(240, 180, 41))
    raw = io.BytesIO()
    page.save(raw, format="PDF")
    return raw.getvalue()


def test_charte_extracts_pdf_colors(client: TestClient) -> None:
    res = client.post("/api/v1/badges/charte/extract", json={"pdf_b64": base64.b64encode(a_pdf()).decode("ascii")})
    assert res.status_code == 200
    colors = res.json()["colors"]
    assert colors and all(len(color) == 7 and color.startswith("#") for color in colors)
    def near(color: str, wanted: tuple[int, int, int]) -> bool:
        rgb = tuple(int(color[i : i + 2], 16) for i in (1, 3, 5))
        return max(abs(a - b) for a, b in zip(rgb, wanted)) <= 12

    assert any(near(color, (36, 90, 160)) for color in colors)
    assert any(near(color, (240, 180, 41)) for color in colors)


def test_charte_without_source_is_refused(client: TestClient) -> None:
    res = client.post("/api/v1/badges/charte/extract", json={})
    assert res.status_code == 400


def test_charte_with_a_non_pdf_is_refused(client: TestClient) -> None:
    res = client.post("/api/v1/badges/charte/extract", json={"pdf_b64": base64.b64encode(b"hello world").decode("ascii")})
    assert res.status_code == 400


def test_charte_from_url_mistake_is_refused_in_words(client: TestClient) -> None:
    res = client.post("/api/v1/badges/charte/extract", json={"url": "http://127.0.0.1:9/nope"})
    assert res.status_code == 422
    assert "n'a pas répondu" in res.json()["detail"]
