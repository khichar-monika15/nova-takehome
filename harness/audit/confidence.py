"""Confidence: our probability that the verdict and the amount are both right, from evidence features."""
from __future__ import annotations

from .rules import Candidate

BASE = {"finding": 0.92, "conflict": 0.8, "cannot_determine": 0.75}


def score(c: Candidate) -> float:
    f = c.features
    p = BASE.get(c.verdict, 0.5)
    if c.cls == "overcharge" and c.verdict == "finding":
        p -= {"tracking": 0.0, "status_email": 0.02, "awb": 0.06, "invoice": 0.15}.get(f.get("pickup_source"), 0.1)
    if f.get("judgment"):
        p -= 0.07
    if f.get("inr"):
        p -= 0.05
    if f.get("lane_from_record"):
        p -= 0.05
    if not c.evidence:
        p -= 0.3
    if c.learned_at:
        p -= 0.02
    return round(min(max(p, 0.05), 0.98), 3)
