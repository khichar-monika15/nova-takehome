"""feedback: keep a person's decisions on disk and apply them to exactly the keys they name."""
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from . import state
from .rules import Candidate
from .world import norm_id


def _path(state_dir) -> Path:
    return Path(state_dir) / "feedback.json"


def load(state_dir) -> list[dict]:
    return state.read_json(_path(state_dir), [])


def store(feedback_file, state_dir) -> None:
    doc = json.loads(Path(feedback_file).read_text())
    items = {i["item_id"]: i for i in load(state_dir)}
    for it in doc.get("items", []):
        items[it["item_id"]] = {**it, "batch": doc.get("after_batch", ""), "decided_at": doc.get("decided_at")}
    state.write_json(_path(state_dir), list(items.values()))


def matches(c: Candidate, key: dict) -> bool:
    if key.get("class") and key["class"] != c.cls:
        return False
    if key.get("invoice_id") and norm_id(key["invoice_id"]) != norm_id(c.invoice_id or ""):
        return False
    for field in ("contract_id", "period", "credit_type"):
        if key.get(field) and str(key[field]).upper() != str(getattr(c, field) or "").upper():
            return False
    return True


def apply(cands: list[Candidate], items: list[dict]) -> list[Candidate]:
    out = []
    for c in cands:
        keep = True
        for fb in items:
            if not matches(c, fb.get("finding_key", {})):
                continue
            decision = fb.get("decision")
            if decision in ("close", "reject"):
                keep = False
            elif decision == "override_amount":
                amount = fb.get("fact", {}).get("value", {}).get("amount_usd")
                if amount is not None:
                    c.amount = Decimal(str(amount))
                    c.learned_at = {"feedback_item_id": fb["item_id"], "batch": fb.get("batch", "")}
        if keep:
            out.append(c)
    return out
