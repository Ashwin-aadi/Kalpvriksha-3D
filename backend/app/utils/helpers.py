import re


def clean_text(text: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', text)   # strip HTML
    text = re.sub(r'\s+', ' ', text)        # collapse spaces
    return text.strip()


def truncate(text: str, max_chars: int = 500) -> str:
    return text[:max_chars] + '...' if len(text) > max_chars else text


def safe_get(d: dict, *keys, default=None):
    for key in keys:
        if isinstance(d, dict):
            d = d.get(key, default)
        else:
            return default
    return d
