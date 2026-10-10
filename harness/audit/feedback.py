"""feedback: keep a person's decisions on disk and apply them to exactly the keys they name."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import state
from .rules import Candidate
from .world import dec, norm_id


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
            try:
                if not matches(c, fb.get("finding_key") or {}):
                    continue
                decision = fb.get("decision")
                if decision in ("close", "reject"):
                    keep = False
                elif decision == "override_amount":
                    amount = dec(((fb.get("fact") or {}).get("value") or {}).get("amount_usd"))
                    if amount is not None:
                        c.amount = amount
                        c.learned_at = {"feedback_item_id": fb["item_id"], "batch": fb.get("batch", "")}
            except (AttributeError, KeyError, TypeError) as e:
                print(f"feedback: skipped malformed item {fb.get('item_id') if isinstance(fb, dict) else fb}: {e}",
                      file=sys.stderr)
        if keep:
            out.append(c)
    return out
