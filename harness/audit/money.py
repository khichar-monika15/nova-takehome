from __future__ import annotations

import re
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

_NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?|-?\.\d+")
_ISO = re.compile(r"\d{4}-\d{2}-\d{2}")
_TEXT_DATE_FORMATS = ("%d %b %Y", "%d %B %Y", "%B %d, %Y", "%b %d, %Y")


def D(x) -> Decimal:
    if isinstance(x, Decimal):
        return x
    if isinstance(x, (int, float)):
        return Decimal(str(x))
    m = _NUM.search(str(x))
    if not m:
        raise ValueError(f"no number in {x!r}")
    return Decimal(m.group(0).replace(",", ""))


def cents(x: Decimal) -> Decimal:
    return D(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def fmt(x) -> str:
    return f"{cents(D(x)):.2f}"


def parse_date(s, fmt_: str | None = None) -> date | None:
    if s is None:
        return None
    if isinstance(s, datetime):
        return s.date()
    if isinstance(s, date):
        return s
    s = str(s).strip()
    if fmt_:
        try:
            return datetime.strptime(s, fmt_).date()  # noqa: DTZ007  date only
        except ValueError:
            return None
    m = _ISO.search(s)
    if m:
        try:
            return date.fromisoformat(m.group(0))
        except ValueError:
            return None
    for f in _TEXT_DATE_FORMATS:
        try:
            return datetime.strptime(s, f).date()  # noqa: DTZ007  date only
        except ValueError:
            continue
    return None


def ceil_div(a: int, b: int) -> int:
    return -(-a // b)
