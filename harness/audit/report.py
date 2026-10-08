"""report: run every rule over the as-of view and print one schema-valid report."""
from __future__ import annotations

import json
import sys
import time
import traceback
from datetime import date, datetime
from pathlib import Path

import jsonschema

from . import actions, confidence, feedback, state
from .ingest import retry_failed
from .money import fmt
from .quotes import long_enough
from .rules import Candidate, cashback, duplicate, expiry, late_fees, overcharge, waiver
from .world import World, build, norm_id

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "grader" / "schema" / "report.schema.json"
RETRY_START_S = 300
RETRY_DEADLINE_S = 420
VERDICT_RANK = {"finding": 0, "conflict": 1, "cannot_determine": 2}


def _schema():
    full = json.loads(SCHEMA_PATH.read_text())
    return full, jsonschema.Draft202012Validator(full)


def _received_by(rec: dict, as_of: date) -> bool:
    return datetime.fromisoformat(rec["received_at"]).date() <= as_of


def _feedback_by(items: list[dict], as_of: date) -> list[dict]:
    out = []
    for it in items:
        decided = (it.get("decided_at") or "")[:10]
        if not decided or date.fromisoformat(decided) <= as_of:
            out.append(it)
    return out


def _safe(name: str, fn, *args) -> list[Candidate]:
    """One rule that fails on unexpected facts loses its own items; the other rules and the report go on."""
    try:
        return fn(*args)
    except Exception:  # noqa: BLE001
        print(f"report: rule {name} failed and was skipped:\n{traceback.format_exc()}", file=sys.stderr)
        return []


def _candidates(w: World) -> list[Candidate]:
    invoice_items = feedback.apply(_safe("overcharge", overcharge.run, w) + _safe("duplicate", duplicate.run, w)
                                   + _safe("waiver", waiver.run, w), w.feedback)
    portfolio = feedback.apply(_safe("late_fees", late_fees.run, w, invoice_items) + _safe("cashback", cashback.run, w)
                               + _safe("expiry", expiry.run, w), w.feedback)
    by_key: dict[tuple, Candidate] = {}
    for c in invoice_items + portfolio:
        old = by_key.get(c.key)
        if old is None or VERDICT_RANK[c.verdict] < VERDICT_RANK[old.verdict]:
            by_key[c.key] = c
    return list(by_key.values())


def _key_str(c: Candidate) -> str:
    return "|".join(str(x) for x in c.key)


def _state_of(c: Candidate) -> list:
    rng = [fmt(x) for x in c.amount_range] if c.amount_range else None
    return [c.verdict, fmt(c.amount) if c.amount is not None else None, rng]


def _base_id(c: Candidate) -> str:
    if c.cls == "cashback":
        return f"cashback:{c.contract_id}/{c.period}/{c.credit_type}"
    if c.cls == "expiry":
        return f"expiry:{c.contract_id}"
    return f"{c.cls}:{norm_id(c.invoice_id or '')}"


def _is_retro(c: Candidate, w: World, prev_as_of: date | None) -> bool:
    """New key that exists only because a document received after the last report reaches back before it."""
    if prev_as_of is None:
        return False
    docs = {d.ref: d for d in w.docs}
    late = [docs[e["doc"]] for e in c.evidence if e["doc"] in docs and docs[e["doc"]].received_at.date() > prev_as_of]
    old = [docs[e["doc"]] for e in c.evidence if e["doc"] in docs and docs[e["doc"]].received_at.date() <= prev_as_of]
    backdated = any(d.kind == "contract" and (d.facts.get("terms", {}).get("effective_date") or "9999") <=
                    prev_as_of.isoformat() for d in late)
    return backdated and any(d.kind == "invoice" for d in old)


def _evidence(c: Candidate) -> list[dict]:
    good = [e for e in c.evidence if long_enough(e["quote"])]
    return good or c.evidence[:1]


def _item(c: Candidate, ident: str, supersedes: list[str], retro: bool) -> dict:
    item = {"id": ident, "class": c.cls, "verdict": c.verdict,
            "amount_usd": fmt(c.amount) if c.amount is not None and c.cls != "expiry" else None,
            "amount_range": [fmt(x) for x in c.amount_range] if c.amount_range else None,
            "deadline": c.deadline.isoformat() if c.deadline else None,
            "action": c.action, "confidence": c.confidence, "evidence": _evidence(c),
            "missing_doc": None, "supersedes": supersedes, "learned_at": c.learned_at}
    if c.invoice_id:
        item["invoice_id"] = norm_id(c.invoice_id)
    if c.contract_id and c.cls in ("cashback", "expiry"):
        item["contract_id"] = c.contract_id
    if c.cls == "cashback":
        item["period"], item["credit_type"] = c.period, c.credit_type
    if c.missing_doc:
        holder = {k: v for k, v in (c.missing_doc.get("holder") or {}).items() if v}
        item["missing_doc"] = {"name": c.missing_doc["name"], "holder": holder or {"party": "carrier"}}
    if retro:
        item["retro"] = True
    return item


def build_report(records: list[dict], fb: list[dict], as_of: date, mode: str, history: dict) -> tuple[dict, dict]:
    """Pure core of `report`: -> (report, updated history)."""
    w = build([r for r in records if _received_by(r, as_of)], as_of, _feedback_by(fb, as_of))
    cands = _candidates(w)
    actions.assign(cands, mode, as_of)
    prev_as_of = date.fromisoformat(history["as_of"]) if history.get("as_of") else None
    keys = dict(history.get("keys", {}))
    report = {"schema_version": "1.0", "as_of": as_of.isoformat(), "mode": mode, "findings": [],
              "portfolio": {"cashback": [], "expiry": [], "late_fee_risk": []}}
    full, _ = _schema()
    item_validator = jsonschema.Draft202012Validator({**full["$defs"]["item"], "$defs": full["$defs"]})
    for c in sorted(cands, key=_key_str):
        c.confidence = confidence.score(c)
        k, now = _key_str(c), _state_of(c)
        prev = keys.get(k)
        if prev is None:
            ident, version, supersedes = _base_id(c), 1, []
        elif prev["state"] != now:
            version = prev["version"] + 1
            ident, supersedes = f"{_base_id(c)}:v{version}", [prev["id"]]
        else:
            ident, version, supersedes = prev["id"], prev["version"], []
        item = _item(c, ident, supersedes, prev is None and _is_retro(c, w, prev_as_of))
        errors = list(item_validator.iter_errors(item))
        if errors:
            print(f"report: dropped {ident}: {errors[0].message}", file=sys.stderr)
            continue
        keys[k] = {"id": ident, "version": version, "state": now}
        if c.cls == "cashback":
            report["portfolio"]["cashback"].append(item)
        elif c.cls == "expiry":
            report["portfolio"]["expiry"].append(item)
        elif c.cls == "late_fee_risk":
            report["portfolio"]["late_fee_risk"].append(item)
        else:
            report["findings"].append(item)
    new_history = history if prev_as_of and as_of < prev_as_of else {"as_of": as_of.isoformat(), "keys": keys}
    return report, new_history


def _empty(as_of: str, mode: str) -> dict:
    return {"schema_version": "1.0", "as_of": as_of, "mode": mode, "findings": [],
            "portfolio": {"cashback": [], "expiry": [], "late_fee_risk": []}}


def report(as_of: str, mode: str, state_dir: str) -> dict:
    state_dir = Path(state_dir)
    t0 = time.monotonic()
    try:
        retry_failed(state_dir, budget_s=RETRY_START_S, deadline_s=RETRY_DEADLINE_S)
    except Exception:  # noqa: BLE001
        print(f"report: retry of failed documents stopped:\n{traceback.format_exc()}", file=sys.stderr)
    day = date.fromisoformat(as_of)
    hist_path = state_dir / "reports" / f"history-{mode}.json"
    try:
        rep, hist = build_report(state.load_docs(state_dir, day), feedback.load(state_dir), day, mode,
                                 state.read_json(hist_path, {}))
    except Exception:  # noqa: BLE001  a report must always print valid JSON
        print(f"report: build failed, printing an empty report:\n{traceback.format_exc()}", file=sys.stderr)
        return _empty(as_of, mode)
    state.write_json(hist_path, hist)
    _, validator = _schema()
    validator.validate(rep)
    items = rep["findings"] + [x for v in rep["portfolio"].values() for x in v]
    reported = [x for x in items if x["verdict"] in ("finding", "conflict", "cannot_determine")]
    to_person = [x for x in reported if x["action"] in ("escalate", "human_review")]
    share = len(to_person) / len(reported) if reported else 0.0
    print(f"report: {len(items)} items in {time.monotonic() - t0:.0f} s; {len(to_person)} of {len(reported)} "
          f"({share:.0%}) go to a person (the cap is 60%)", file=sys.stderr)
    return rep
