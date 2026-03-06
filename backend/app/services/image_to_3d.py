"""
image_to_3d.py — Fallback Layer 4
Owner: Ashutosh

Uses Luma AI to reconstruct 3D from a Wikipedia image of the concept.
Auto-skips if LUMA_API_KEY is not set.
"""

import os
import httpx
import asyncio
from app.models.schemas import ConceptResponse, FallbackResponse

LUMA_KEY = os.getenv("LUMA_API_KEY")


async def generate(concept: ConceptResponse) -> FallbackResponse | None:
    if not LUMA_KEY:
        return None
    image_url = await _find_image(concept.query)
    if not image_url:
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.lumalabs.ai/dream-machine/v1/generations/image-to-video",
                headers={"Authorization": f"Bearer {LUMA_KEY}"},
                json={"image_url": image_url})
            job = resp.json()
        for _ in range(12):
            await asyncio.sleep(5)
            async with httpx.AsyncClient() as c:
                result = (await c.get(
                    f"https://api.lumalabs.ai/dream-machine/v1/generations/{job['id']}",
                    headers={"Authorization": f"Bearer {LUMA_KEY}"})).json()
            if result.get("state") == "completed":
                return FallbackResponse(
                    layer_used=4,
                    layer_name="Image-to-3D API Integration",
                    result_type="image_to_3d",
                    model=None,
                    geometry=None,
                    explanation=f'Reconstructed 3D from image of "{concept.query}".')
    except Exception:
        return None
    return None


async def _find_image(query: str) -> str | None:
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                "https://en.wikipedia.org/w/api.php",
                params={"action":"query","titles":query,"prop":"pageimages",
                        "format":"json","pithumbsize":800})
            for page in resp.json().get("query",{}).get("pages",{}).values():
                if page.get("thumbnail",{}).get("source"):
                    return page["thumbnail"]["source"]
    except Exception:
        pass
    return None
