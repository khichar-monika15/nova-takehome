"""Make every evidence quote one the grader can find on the cited page."""
from __future__ import annotations

from difflib import SequenceMatcher

MIN_RATIO = 0.9
MAX_WINDOW = 4


def norm(s: str) -> str:
    return " ".join(s.split())


def long_enough(quote: str) -> bool:
    return len("".join(quote.split())) >= 12


def _windows(page: str):
    lines = [norm(x) for x in page.split("\n") if x.strip()]
    for size in range(1, MAX_WINDOW + 1):
        for i in range(len(lines) - size + 1):
            yield " ".join(lines[i:i + size])


def locate(pages: list[str], page: int, quote: str) -> tuple[int, str] | None:
    """-> (page, quote) where the quote is on that page, repaired to the page's own text, or None."""
    q = norm(quote)
    if not q:
        return None
    order = [page] + [i for i in range(1, len(pages) + 1) if i != page] if 1 <= page <= len(pages) \
        else list(range(1, len(pages) + 1))
    for p in order:
        if q in norm(pages[p - 1]):
            return p, quote
    best: tuple[float, int, str] | None = None
    for p in order:
        for w in _windows(pages[p - 1]):
            if abs(len(w) - len(q)) > max(8, len(q) // 5):
                continue
            r = SequenceMatcher(None, q, w).ratio()
            if r >= MIN_RATIO and (best is None or r > best[0]):
                best = (r, p, w)
    return (best[1], best[2]) if best else None


def line_with(pages: list[str], *needles: str) -> tuple[int, str] | None:
    for p, text in enumerate(pages, 1):
        for line in text.split("\n"):
            if all(n in line for n in needles):
                return p, line.strip()
    return None
