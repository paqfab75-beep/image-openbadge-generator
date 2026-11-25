"""The badge generator's routes: charte analysis to prefill the form's colors, then generation."""

import base64
import binascii

import httpx
from fastapi import APIRouter, HTTPException

from api.badgegen import charte, fonts, renderer
from api.badgegen.models import BadgeSpec, CharteRequest, CharteResponse, GeneratedBadge

router = APIRouter()


@router.post(
    "/charte/extract",
    operation_id="badge_charte_extract",
    summary="Extraire une palette de couleurs d'un PDF de charte ou d'un site web de référence",
    description="Rend les couleurs dominantes pour préremplir les zones de couleurs du formulaire.",
)
async def extract_charte(request: CharteRequest) -> CharteResponse:
    if not request.pdf_b64 and not request.url:
        raise HTTPException(status_code=400, detail="Donnez un PDF encodé en base64 ou l'URL d'un site de référence.")
    try:
        if request.pdf_b64:
            try:
                raw = base64.b64decode(request.pdf_b64, validate=True)
            except (binascii.Error, ValueError) as error:
                raise HTTPException(status_code=400, detail="Le PDF n'est pas encodé en base64 valide.") from error
            if not raw.startswith(b"%PDF"):
                raise HTTPException(status_code=400, detail="Le fichier joint n'est pas un PDF.")
            return CharteResponse(colors=charte.extract_from_pdf(raw))
        return CharteResponse(colors=charte.extract_from_url(request.url))  # type: ignore[arg-type]
    except charte.CharteExtractionError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except httpx.HTTPError as error:
        raise HTTPException(status_code=422, detail=f"Le site de référence n'a pas répondu correctement : {error}") from error


@router.post(
    "/generate",
    operation_id="badge_generate",
    summary="Générer le badge : PNG carré de 1000×1000 px, 250 Ko maximum",
    description="Reçoit une spécification complète de badge (titre, forme, pictos, couleurs, fond) et répond l'image PNG encodée en base64.",
)
async def generate_badge(spec: BadgeSpec) -> GeneratedBadge:
    try:
        image, png = renderer.render(spec)
    except (renderer.BackgroundImageError, fonts.GlyphCoverageError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return GeneratedBadge(png_b64=base64.b64encode(png).decode("ascii"), size_bytes=len(png))
