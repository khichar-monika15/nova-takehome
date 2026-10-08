"""The action for each item, per mode, by the glossary's action table and unattended-action test."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from .rules import Candidate

THRESHOLD = Decimal("5000.00")
VERB = {"overcharge": "dispute", "duplicate": "dispute", "waived_but_billed": "dispute",
        "late_fee_not_owed": "dispute", "cashback": "claim_credit"}
CARRIER_RECORD_SOURCES = ("tracking", "status_email")


def _group(c: Candidate) -> tuple:
    return ("invoice", c.invoice_id.upper()) if c.invoice_id else c.key


def _internal(c: Candidate, as_of: date) -> str | None:
    if c.cls == "expiry":
        return "internal:alert"
    if c.cls == "late_fee_risk":
        return "internal:payment_reminder"
    if c.cls == "cashback" and c.due and c.due > as_of:
        return "internal:track_credit"
    return None


def _verb(c: Candidate) -> str | None:
    if c.verdict == "cannot_determine":
        return "request_document"
    return VERB.get(c.cls) if c.verdict == "finding" else None


def _unattended_ok(c: Candidate, conflicts: set[tuple]) -> bool:
    f = c.features
    if not c.evidence:
        return False
    if c.verdict == "finding" and c.cls == "overcharge" and f.get("pickup_source") not in CARRIER_RECORD_SOURCES:
        return False
    return not any((c.contract_id, lane) in conflicts for lane in f.get("lanes", ()))


def assign(cands: list[Candidate], mode: str, as_of: date) -> None:
    outbound_total: dict[tuple, Decimal] = {}
    for c in cands:
        if c.verdict == "finding" and _verb(c) and not _internal(c, as_of) and c.amount is not None:
            outbound_total[_group(c)] = outbound_total.get(_group(c), Decimal(0)) + c.amount
    conflicts = {(c.contract_id, lane) for c in cands if c.verdict == "conflict"
                 for lane in c.features.get("lanes", ())}
    for c in cands:
        if c.verdict == "conflict":
            c.action = "escalate"
            continue
        if c.verdict not in ("finding", "cannot_determine"):
            c.action = "none"
            continue
        internal = _internal(c, as_of) if c.verdict == "finding" else None
        if internal:
            c.action = internal
            continue
        verb = _verb(c)
        if outbound_total.get(_group(c), Decimal(0)) >= THRESHOLD:
            c.action = "human_review"
        elif mode == "autonomous":
            c.action = f"execute:{verb}" if _unattended_ok(c, conflicts) else "human_review"
        else:
            c.action = f"draft:{verb}"
        if mode != "autonomous" and c.action.startswith("execute:"):
            c.action = f"draft:{verb}"
