"""
retrieval_service.py — Sketchfab Retrieval
Strategy:
  1. Search with EXACT concept name first (short, clean)
  2. Search with concept + 2 keywords second
  3. Merge, deduplicate, return up to 20 results
  Short queries work better on Sketchfab than long verbose ones.
"""

import os
import httpx
from app.models.schemas import ConceptResponse

LOCAL_INDEX = [
    {"id": "local-heart",  "name": "Human Heart",  "tags": ["heart","cardiac","organ","biology"],  "embed_url": None},
    {"id": "local-dna",    "name": "DNA",           "tags": ["dna","helix","genetics","biology"],   "embed_url": None},
    {"id": "local-solar",  "name": "Solar System",  "tags": ["solar","planet","astronomy","space"], "embed_url": None},
    {"id": "local-taj",    "name": "Taj Mahal",     "tags": ["taj","mahal","india","architecture"], "embed_url": None},
]


async def _sketchfab_search(query: str, sketchfab_key: str, count: int = 10) -> list:
    """Single Sketchfab search call."""
    headers = {"Authorization": f"Token {sketchfab_key}"}
    params = {
        "q": query,
        "type": "models",
        "downloadable": "false",
        "sort_by": "-likeCount",
        "count": count,
    }
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(
                "https://api.sketchfab.com/v3/search",
                headers=headers,
                params=params,
            )
            r.raise_for_status()
            data = r.json()

        results = []
        for item in data.get("results", []):
            uid = item.get("uid")
            if not uid:
                continue
            embed_url = (
                f"https://sketchfab.com/models/{uid}/embed"
                f"?autostart=1&ui_hint=0&ui_controls=1&ui_infos=0&ui_watermark=0&preload=1"
            )
            thumbnails = item.get("thumbnails", {}).get("images", [])
            thumb = thumbnails[0].get("url", "") if thumbnails else ""
            results.append({
                "id": uid,
                "name": item.get("name", "Unknown"),
                "embed_url": embed_url,
                "thumbnail": thumb,
                "like_count": item.get("likeCount", 0),
                "source": "sketchfab",
            })
        return results
    except Exception as e:
        print(f"[retrieval] Sketchfab search failed for '{query}': {e}")
        return []


async def search_sketchfab(concept: ConceptResponse) -> list:
    """
    Dual search strategy:
    - Query 1: exact concept name (e.g. "human heart")
    - Query 2: concept + top keyword (e.g. "human heart anatomy")
    Merge and deduplicate results.
    """
    sketchfab_key = os.getenv("SKETCHFAB_API_KEY", "")
    if not sketchfab_key or sketchfab_key.startswith("<"):
        print("[retrieval] No SKETCHFAB_API_KEY set — skipping Sketchfab search")
        return []

    # Query 1: just the concept name — clean and short
    query1 = concept.query.strip()

    # Query 2: concept name + first useful keyword
    extra = ""
    for kw in concept.search_keywords:
        kw_clean = kw.lower().strip()
        # Skip if keyword is already in the query
        if kw_clean not in query1.lower() and len(kw_clean) > 2:
            extra = kw_clean
            break
    query2 = f"{query1} {extra}".strip() if extra else ""

    print(f"[retrieval] Search 1: '{query1}'")
    results1 = await _sketchfab_search(query1, sketchfab_key, count=12)

    results2 = []
    if query2 and query2 != query1:
        print(f"[retrieval] Search 2: '{query2}'")
        results2 = await _sketchfab_search(query2, sketchfab_key, count=8)

    # Merge and deduplicate by uid
    seen_ids = set()
    merged = []
    for r in results1 + results2:
        if r["id"] not in seen_ids:
            seen_ids.add(r["id"])
            merged.append(r)

    print(f"[retrieval] Sketchfab returned {len(merged)} unique results for: '{query1}'")
    return merged


def search_local(keywords: list) -> list:
    results = []
    kw_lower = [k.lower() for k in keywords]
    for item in LOCAL_INDEX:
        score = sum(1 for kw in kw_lower if any(kw in tag for tag in item["tags"]))
        if score > 0:
            results.append({**item, "score": score, "source": "local"})
    results.sort(key=lambda x: x["score"], reverse=True)
    return results


async def retrieve(concept: ConceptResponse) -> list:
    """Main retrieval entry point."""
    results = await search_sketchfab(concept)

    if not results:
        # Fall back to local index
        keywords = (
            [concept.query]
            + concept.search_keywords
            + concept.related_terms[:3]
            + concept.components[:3]
        )
        results = search_local(keywords)

    return results