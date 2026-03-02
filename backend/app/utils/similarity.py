def normalize_score(raw_cosine: float) -> float:
    return round(max(0.0, min(1.0, raw_cosine)) * 100, 1)


def text_overlap_score(expected: list[str], text: str) -> float:
    if not expected:
        return 0.0
    found = sum(1 for c in expected if c.lower() in text.lower())
    return round((found / len(expected)) * 100, 1)


def combined_score(cosine: float, overlap: float,
                   w_cos=0.7, w_ovl=0.3) -> float:
    return round(cosine * w_cos + overlap * w_ovl, 1)
